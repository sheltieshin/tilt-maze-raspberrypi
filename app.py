# app.py
import time
import threading
import logging
from flask import Flask, request, jsonify, send_from_directory

import RPi.GPIO as GPIO

import config
from pca9685_raw import PCA9685Raw
from gimbal import Gimbal, ServoEndpoint

# 關閉 Flask / Werkzeug 的 request log
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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
BUTTON_PIN = getattr(config, "BUTTON_GPIO", 17)  # GPIO17 <-> switch <-> GND (PUD_UP)
BUZZER_GPIO = 22  # 你已確認硬體接在 GPIO22

goal_triggered = False
goal_time = 0.0

# --- IR state ---
_won = False
_ir_active_high = config.IR_ACTIVE_HIGH

# --- GPIO ready guard ---
_gpio_ready = False
_gpio_lock = threading.Lock()

# --- Buzzer guard (avoid being cut off by other endpoints) ---
buzzer_lock = threading.Lock()
_beeping = False


def gpio_init():
    """GPIO 初始化（不包含 LED）"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # IR
    GPIO.setup(config.IR_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # BUZZER
    GPIO.setup(BUZZER_GPIO, GPIO.OUT)
    GPIO.output(BUZZER_GPIO, GPIO.LOW)

    # GOAL button
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    global _gpio_ready
    _gpio_ready = True


def ensure_gpio():
    global _gpio_ready
    if _gpio_ready:
        return
    with _gpio_lock:
        if not _gpio_ready:
            gpio_init()


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

    idle = 1 if sum(samples) > (len(samples) // 2) else 0
    return (idle == 0)  # idle==0 => active-high likely


def ir_triggered():
    v = GPIO.input(config.IR_GPIO)
    return (v == 1) if _ir_active_high else (v == 0)


def beep(duration=0.8):
    """主動蜂鳴器：HIGH 即發聲"""
    global _beeping
    with buzzer_lock:
        _beeping = True
        GPIO.output(BUZZER_GPIO, True)
        time.sleep(duration)
        GPIO.output(BUZZER_GPIO, False)
        _beeping = False


def celebrate():
    """IR 過關：只做蜂鳴器提示（不使用 LED）"""
    global _beeping
    with buzzer_lock:
        _beeping = True
        for _ in range(2):
            GPIO.output(BUZZER_GPIO, True)
            time.sleep(0.12)
            GPIO.output(BUZZER_GPIO, False)
            time.sleep(0.10)
        _beeping = False


def goal_watcher():
    """
    Edge trigger: 1->0 觸發一次 GOAL
    並且先等按鍵穩定為「未按下(=1)」1 秒再開始監聽。
    """
    global goal_triggered, goal_time

    # 開機先等按鍵穩定（未按下=1）
    stable = 0
    while stable < 50:
        if GPIO.input(BUTTON_PIN) == 1:
            stable += 1
        else:
            stable = 0
        time.sleep(0.02)

    last = GPIO.input(BUTTON_PIN)

    while True:
        now = GPIO.input(BUTTON_PIN)

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
            try:
                beep(0.8)
            finally:
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
    ensure_gpio()
    global goal_triggered, goal_time
    goal_triggered = False
    goal_time = 0.0
    try:
        gimbal.center()
    except Exception:
        pass
    return jsonify({"ok": True})


@app.route("/api/center", methods=["POST"])
def api_center():
    """
    回中立：不碰 LED。
    GOAL 或正在 beep 時，不要硬關蜂鳴器。
    """
    ensure_gpio()
    global _won, _beeping
    _won = False

    # ✅ 防止掐掉正在發聲的蜂鳴器
    if (not _beeping) and (not goal_triggered):
        GPIO.output(BUZZER_GPIO, GPIO.LOW)

    x_pwm, y_pwm = gimbal.center()
    return jsonify({"ok": True, "x_pwm": x_pwm, "y_pwm": y_pwm, "ir_active_high": _ir_active_high})


@app.route("/api/tilt", methods=["POST"])
def api_tilt():
    ensure_gpio()
    global _won, goal_triggered

    # ✅ GOAL 鎖定：goal 後不再讓伺服動
    if goal_triggered:
        return jsonify({"locked": True, "goal": True})

    data = request.get_json(force=True) or {}
    x = float(data.get("x", 0.0))
    y = float(data.get("y", 0.0))

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

    if _ir_active_high is None:
        _ir_active_high = detect_ir_polarity()

    threading.Thread(target=goal_watcher, daemon=True).start()

    context = (config.CERT_FILE, config.KEY_FILE)
    app.run(host=config.HOST, port=config.PORT, ssl_context=context, threaded=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        GPIO.cleanup()

