# app.py
import time
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

# --- GPIO setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(config.IR_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # safe default
GPIO.setup(config.LED_GPIO, GPIO.OUT)
GPIO.setup(config.BUZZER_GPIO, GPIO.OUT)

GPIO.output(config.LED_GPIO, GPIO.LOW)
GPIO.output(config.BUZZER_GPIO, GPIO.LOW)

_won = False
_ir_active_high = config.IR_ACTIVE_HIGH

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

if _ir_active_high is None:
    _ir_active_high = detect_ir_polarity()

def ir_triggered():
    v = GPIO.input(config.IR_GPIO)
    return (v == 1) if _ir_active_high else (v == 0)

def celebrate():
    GPIO.output(config.LED_GPIO, GPIO.HIGH)
    # beep pattern
    for _ in range(2):
        GPIO.output(config.BUZZER_GPIO, GPIO.HIGH)
        time.sleep(0.12)
        GPIO.output(config.BUZZER_GPIO, GPIO.LOW)
        time.sleep(0.10)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/center", methods=["POST"])
def api_center():
    global _won
    _won = False
    GPIO.output(config.LED_GPIO, GPIO.LOW)
    GPIO.output(config.BUZZER_GPIO, GPIO.LOW)
    x_pwm, y_pwm = gimbal.center()
    return jsonify({"ok": True, "x_pwm": x_pwm, "y_pwm": y_pwm, "ir_active_high": _ir_active_high})

@app.route("/api/tilt", methods=["POST"])
def api_tilt():
    global _won
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
    # HTTPS server
    context = (config.CERT_FILE, config.KEY_FILE)
    app.run(host=config.HOST, port=config.PORT, ssl_context=context, threaded=True)

if __name__ == "__main__":
    try:
        main()
    finally:
        GPIO.cleanup()

