# app.py
import time
import threading
from flask import Flask, request, jsonify, send_from_directory

import RPi.GPIO as GPIO

import config
from pca9685_raw import PCA9685Raw
from gimbal import Gimbal, ServoEndpoint

app = Flask(__name__, static_folder="static")

# --- PCA + Gimbal ---
pca = PCA9685Raw(address=config.PCA_ADDR, freq_hz=50)

servo_x = ServoEndpoint(
    ch=config.SERVO_X_CH,
    pwm_min=config.X_MIN,
    pwm_max=config.X_MAX,
    scale=config.X_SCALE
)
servo_x.pwm_center = config.X_CENTER

servo_y = ServoEndpoint(
    ch=config.SERVO_Y_CH,
    pwm_min=config.Y_MIN,
    pwm_max=config.Y_MAX,
    scale=config.Y_SCALE
)
servo_y.pwm_center = config.Y_CENTER

gimbal = Gimbal(pca, servo_x, servo_y)
gimbal.center()

# =========================
# GOAL: 微動開關 + 蜂鳴器
# =========================
# 微動開關：GPIO17 <-> 開關 <-> GND（用內建上拉）
BUTTON_PIN = getattr(config, "BUTTON_GPIO", 17)

# 蜂鳴器：優先沿用你原本 config 的 BUZZER_GPIO（常見就是 22）
BUZZER_PIN = getattr(config, "BUZZER_GPIO", 22)

buzzer_lock = threading.Lock()

goal_triggered = False
goal_time = 0.0

# --- IR/LED/Buzzer state ---
_won = False
_ir_active_high = config.IR_ACTIVE_HIGH


def gpio_init():
    """
    統一在 main() 啟動時做 GPIO 初始化，避免 import 時就動 GPIO。
    """
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # IR / LED / BUZZER（你原本的）
    GPIO.setup(config.IR_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # safe default
    GPIO.setup(config.LED_GPIO, GPIO.OUT)
    GPIO.setup(config.BUZZER_GPIO, GPIO.OUT)

    GPIO.output(config.LED_GPIO, GPIO.LOW)
    #GPIO.output(config.BUZZER_GPIO, GPIO.LOW)
    # GOAL beeping 時不要硬切 LOW，避免把蜂鳴器聲音立刻掐掉
    if not goal_triggered:
        GPIO.output(config.BUZZER_GPIO, GPIO.LOW)

    # GOAL Button（新增）
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def detect_ir_polarity():
    """
    Auto-detect IR polarity by sampling stable idle state for a moment.
    We assume the ball is NOT blocking at startup.
    """
    samples = []
    t_end = time.time() + 1.2
    while time.time() < t_end:
        samples.append(GPIO.input(config.IR_GPIO))
        time.sleep(0.02)
    # majority vote
    idle = 1 if sum(samples) > (len(samples) // 2) else 0
    # If idle is 1, then triggered likely 0 (active-low). If idle is 0, triggered likely 1 (active-high).
    return (idle == 0)


def ir_triggered():
    v = GPIO.input(config.IR_GPIO)
    return (v == 1) if _ir_active_high else (v == 0)


def celebrate():
    GPIO.output(config.LED_GPIO, GPIO.HIGH)
    with buzzer_lock:
        for _ in range(2):
            GPIO.output(config.BUZZER_GPIO, GPIO.HIGH)
            time.sleep(0.12)
            GPIO.output(config.BUZZER_GPIO, GPIO.LOW)
            time.sleep(0.10)


def beep(duration=3.0):
    with buzzer_lock:
        GPIO.output(config.BUZZER_GPIO, True)
        time.sleep(duration)
        GPIO.output(config.BUZZER_GPIO, False)


def goal_watcher():
    """
    只在 1->0 的瞬間觸發一次（edge trigger），避免抖動誤判。
    並且先等按鍵穩定為「未按下(=1)」1 秒再開始監聽。
    """
    global goal_triggered, goal_time

    # 開機先等按鍵穩定（未按下=1）
    stable = 0
    while stable < 50:  # 50 * 0.02 = 1s
        if GPIO.input(BUTTON_PIN) == 1:
            stable += 1
        else:
            stable = 0
        time.sleep(0.02)

    last = GPIO.input(BUTTON_PIN)

    while True:
        now = GPIO.input(BUTTON_PIN)

        # edge: 1 -> 0 才觸發（按下）
        if (not goal_triggered) and last == 1 and now == 0:
            goal_triggered = True
            goal_time = time.time()

            # GOAL 後：回中立（避免繼續亂動）
            try:
                gimbal.center()
            except Exception:
                pass

            # 蜂鳴器提示
            print("GOAL edge detected -> beeping...")
            beep(0.8)
            print("beep done")

        last = now
        time.sleep(0.02)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/goal", methods=["GET"])
def api_goal():
    return jsonify({"goal": bool(goal_triggered), "goal_time": goal_time})


@app.route("/api/reset_goal", methods=["POST"])
def api_reset_goal():
    global goal_triggered, goal_time
    goal_triggered = False
    goal_time = 0.0
    try:
        gimbal.center()
    except Exception:
        pass
    return jsonify({"ok": True})

import traceback
@app.route("/api/center", methods=["POST"])
def api_center():
    print("CENTER called! stack:")
    print("".join(traceback.format_stack(limit=8)))
    global _won, goal_triggered
    _won = False
    GPIO.output(config.LED_GPIO, GPIO.LOW)
    if not goal_triggered:
        GPIO.output(config.BUZZER_GPIO, GPIO.LOW)
    x_pwm, y_pwm = gimbal.center()
    return jsonify({"ok": True, "x_pwm": x_pwm, "y_pwm": y_pwm, "ir_active_high": _ir_active_high})

@app.route("/api/tilt", methods=["POST"])
def api_tilt():
    global _won, goal_triggered

    # ✅ GOAL 鎖定：goal 後不再讓伺服動
    if goal_triggered:
        return jsonify({"locked": True, "goal": True})

    data = request.get_json(force=True) or {}
    x = float(data.get("x", 0.0))
    y = float(data.get("y", 0.0))

    # Safety clamp already inside gimbal mapping, but keep here too
    x_pwm, y_pwm = gimbal.set_xy(x, y)

    trig = ir_triggered()
    if trig and not _won:
        _won = True
        celebrate()

    return jsonify({
        "x_pwm": x_pwm,
        "y_pwm": y_pwm,
        "ir_triggered": trig,
        "won": _won,
        "ir_active_high": _ir_active_high
    })


def main():
    global _ir_active_high

    gpio_init()

    # IR polarity auto-detect（一定要在 GPIO init 後）
    if _ir_active_high is None:
        _ir_active_high = detect_ir_polarity()

    # ✅ 啟動 GOAL watcher thread
    threading.Thread(target=goal_watcher, daemon=True).start()

    # HTTPS server
    context = (config.CERT_FILE, config.KEY_FILE)
    app.run(host=config.HOST, port=config.PORT, ssl_context=context, threaded=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        GPIO.cleanup()

