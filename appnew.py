from flask import Flask, request, jsonify, send_from_directory
import threading
import time
import atexit

import RPi.GPIO as GPIO

import config
from gimbal import Gimbal, ServoEndpoint
from pca9685_raw import PCA9685Raw  # 你專案裡 raw PCA 的類別檔名若不同，改這行

# =========================
# GPIO 腳位（BCM）
# =========================
BUTTON_PIN = 17   # 輕觸開關：GPIO17 <-> 按鍵 <-> GND（用內建上拉）
BUZZER_PIN = 22   # 主動蜂鳴器：GPIO22 -> + , GND -> -

LED_PIN = None    # 例如 27；沒接就保持 None

# =========================
# 全域狀態
# =========================
goal_triggered = False
goal_time = 0.0
last_pwm_x = None
last_pwm_y = None

# =========================
# Flask
# =========================
app = Flask(__name__, static_folder="static", static_url_path="")

# =========================
# PCA9685 + Gimbal 初始化
# =========================
pca = PCA9685Raw(address=0x40, bus_id=1, freq_hz=50)
# ⚠️ 如果你的 pca9685_raw.py 裡沒有 set_pwm_freq()，就不要再呼叫
# pca.set_pwm_freq(50)

servo_x = ServoEndpoint(
    ch=0,
    pwm_min=config.X_MIN,
    pwm_max=config.X_MAX,
    scale=getattr(config, "X_SCALE", 1.0),
)
servo_x.pwm_center = getattr(config, "X_CENTER", None)

servo_y = ServoEndpoint(
    ch=2,
    pwm_min=config.Y_MIN,
    pwm_max=config.Y_MAX,
    scale=getattr(config, "Y_SCALE", 1.0),
)
servo_y.pwm_center = getattr(config, "Y_CENTER", None)

gimbal = Gimbal(pca, servo_x, servo_y)


# =========================
# GPIO 初始化
# =========================
def gpio_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.output(BUZZER_PIN, False)

    if LED_PIN is not None:
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, False)


def celebrate(duration=1.0):
    GPIO.output(BUZZER_PIN, True)
    if LED_PIN is not None:
        GPIO.output(LED_PIN, True)

    time.sleep(duration)

    GPIO.output(BUZZER_PIN, False)
    if LED_PIN is not None:
        GPIO.output(LED_PIN, False)


# =========================
# Goal watcher（只觸發一次）
# =========================
def goal_watcher():
    global goal_triggered, goal_time, last_pwm_x, last_pwm_y
    last = GPIO.input(BUTTON_PIN)

    while True:
        now = GPIO.input(BUTTON_PIN)

        # edge: 1 -> 0 才算「剛按下」
        if (not goal_triggered) and last == 1 and now == 0:
            goal_triggered = True
            goal_time = time.time()

            # ✅ GOAL 後立刻回中立（並鎖定 tilt）
            try:
                last_pwm_x, last_pwm_y = gimbal.center()
            except Exception:
                pass

            celebrate(1.0)

        last = now
        time.sleep(0.02)


# =========================
# Routes
# =========================
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/tilt", methods=["POST"])
def api_tilt():
    global goal_triggered, last_pwm_x, last_pwm_y

    data = request.get_json(force=True) or {}
    x = float(data.get("x", 0.0))
    y = float(data.get("y", 0.0))

    # ✅ GOAL 鎖定：不再動
    if goal_triggered:
        return jsonify({
            "locked": True,
            "goal": True,
            "x_pwm": last_pwm_x,
            "y_pwm": last_pwm_y
        })

    try:
        last_pwm_x, last_pwm_y = gimbal.set_xy(x, y)
        return jsonify({
            "locked": False,
            "goal": False,
            "x_pwm": last_pwm_x,
            "y_pwm": last_pwm_y
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/center", methods=["POST"])
def api_center():
    global last_pwm_x, last_pwm_y
    try:
        last_pwm_x, last_pwm_y = gimbal.center()
        return jsonify({"ok": True, "x_pwm": last_pwm_x, "y_pwm": last_pwm_y})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/goal", methods=["GET"])
def api_goal():
    return jsonify({"goal": bool(goal_triggered), "goal_time": goal_time})


@app.route("/api/reset_goal", methods=["POST"])
def api_reset_goal():
    global goal_triggered, goal_time, last_pwm_x, last_pwm_y
    goal_triggered = False
    goal_time = 0.0
    try:
        last_pwm_x, last_pwm_y = gimbal.center()
    except Exception:
        pass
    return jsonify({"ok": True})


def cleanup():
    try:
        GPIO.cleanup()
    except Exception:
        pass


atexit.register(cleanup)


if __name__ == "__main__":
    gpio_init()
    threading.Thread(target=goal_watcher, daemon=True).start()

    # 如果你原本有 HTTPS ssl_context，請把這行改回你原本的 app.run(..., ssl_context=...)
app.run(
    host="0.0.0.0",
    port=8443,
    debug=False,
    threaded=True,
    ssl_context=("cert/cert.pem", "cert/key.pem")
)

