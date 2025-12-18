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
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__, static_folder="static")

# =========================
# PCA + Gimbal
# =========================
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
# GOAL: Reed Switch + Buzzer
# =========================
REED_GPIO = getattr(config, "REED_GPIO", 17)   # 磁簧開關
BUZZER_GPIO = getattr(config, "BUZZER_GPIO", 22)

goal_triggered = False
goal_time = 0.0

_gpio_ready = False
_gpio_lock = threading.Lock()

buzzer_lock = threading.Lock()
_beeping = False


def gpio_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Reed switch (PUD_UP)
    GPIO.setup(REED_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Buzzer
    GPIO.setup(BUZZER_GPIO, GPIO.OUT)
    GPIO.output(BUZZER_GPIO, GPIO.LOW)

    global _gpio_ready
    _gpio_ready = True


def ensure_gpio():
    if _gpio_ready:
        return
    with _gpio_lock:
        if not _gpio_ready:
            gpio_init()

print("GOAL -> BUZZER_GPIO =", BUZZER_GPIO)
def beep(duration=0.8):
    global _beeping
    with buzzer_lock:
        _beeping = True
        GPIO.output(BUZZER_GPIO, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_GPIO, GPIO.LOW)
        _beeping = False


def goal_watcher():
    """
    Reed switch edge trigger:
    1 -> 0 表示磁鐵靠近（球進洞）
    """
    global goal_triggered, goal_time

    # 開機先等「未觸發狀態」穩定（GPIO=1）
    stable = 0
    while stable < 50:
        if GPIO.input(REED_GPIO) == 1:
            stable += 1
        else:
            stable = 0
        time.sleep(0.02)

    last = GPIO.input(REED_GPIO)

    while True:
        now = GPIO.input(REED_GPIO)

        if (not goal_triggered) and last == 1 and now == 0:
            goal_triggered = True
            goal_time = time.time()

            # GOAL 後回中立
            try:
                gimbal.center()
            except Exception:
                pass

            print("🎉 GOAL detected (reed switch)")
            beep(0.8)

        last = now
        time.sleep(0.02)


# =========================
# Flask Routes
# =========================
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
    ensure_gpio()
    x_pwm, y_pwm = gimbal.center()
    return jsonify({"ok": True, "x_pwm": x_pwm, "y_pwm": y_pwm})


@app.route("/api/tilt", methods=["POST"])
def api_tilt():
    ensure_gpio()

    if goal_triggered:
        return jsonify({"locked": True, "goal": True})

    data = request.get_json(force=True) or {}
    x = float(data.get("x", 0.0))
    y = float(data.get("y", 0.0))

    x_pwm, y_pwm = gimbal.set_xy(x, y)

    return jsonify({
        "x_pwm": x_pwm,
        "y_pwm": y_pwm,
        "goal": False
    })


def main():
    gpio_init()
    threading.Thread(target=goal_watcher, daemon=True).start()

    context = (config.CERT_FILE, config.KEY_FILE)
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context=context,
        threaded=True
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        GPIO.cleanup()

