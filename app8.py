from flask import Flask, request, jsonify, send_from_directory
import threading
import time
import atexit

import RPi.GPIO as GPIO

from gimbal import Gimbal  # 你原本就有的雙軸雲台控制（PCA9685 raw）

# =========================
# GPIO 腳位設定（BCM）
# =========================
BUTTON_PIN = 17   # 輕觸開關：一腳接 GPIO17，一腳接 GND
BUZZER_PIN = 22   # 蜂鳴器：+ 接 GPIO22，- 接 GND

# 若你也有 LED，可以打開這兩行並接線
LED_PIN = None    # 例如 27；不用就保持 None

# =========================
# 全域狀態
# =========================
goal_triggered = False
goal_time = 0.0

# =========================
# 初始化 Flask 與雲台
# =========================
app = Flask(__name__, static_folder="static", static_url_path="")

gimbal = Gimbal()  # 依你現有 gimbal.py 建構方式


# =========================
# GPIO 初始化
# =========================
def gpio_init():
    GPIO.setmode(GPIO.BCM)

    # 按鍵：用內建上拉（沒按=1，按下=0）
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.output(BUZZER_PIN, False)

    if LED_PIN is not None:
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, False)


def celebrate(duration=1.0):
    # 蜂鳴器叫 + LED 亮（如果有）
    GPIO.output(BUZZER_PIN, True)
    if LED_PIN is not None:
        GPIO.output(LED_PIN, True)

    time.sleep(duration)

    GPIO.output(BUZZER_PIN, False)
    if LED_PIN is not None:
        GPIO.output(LED_PIN, False)


# =========================
# Goal watcher：偵測「剛按下」才觸發一次
# =========================
def goal_watcher():
    global goal_triggered, goal_time

    last = GPIO.input(BUTTON_PIN)

    while True:
        now = GPIO.input(BUTTON_PIN)

        # edge trigger：從 1 → 0 才算「剛按下」
        if (not goal_triggered) and last == 1 and now == 0:
            goal_triggered = True
            goal_time = time.time()

            # ✅ 立刻回中立，並鎖定（之後 tilt 都不處理）
            try:
                gimbal.center()
            except Exception:
                pass

            # ✅ 蜂鳴器/LED 慶祝
            celebrate(1.0)

        last = now
        time.sleep(0.02)


# =========================
# API
# =========================
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/tilt", methods=["POST"])
def api_tilt():
    """手機送 x,y（-1..1 的比例值），控制雲台。
       GOAL 後會鎖定，不再動。"""
    global goal_triggered

    data = request.get_json(force=True) or {}
    x = float(data.get("x", 0.0))
    y = float(data.get("y", 0.0))

    # ✅ GOAL 鎖定：直接忽略任何 tilt
    if goal_triggered:
        # 仍回傳目前 PWM（或中心點）
        try:
            x_pwm, y_pwm = gimbal.get_last_pwm()
        except Exception:
            x_pwm, y_pwm = None, None
        return jsonify({
            "locked": True,
            "goal": True,
            "x_pwm": x_pwm,
            "y_pwm": y_pwm
        })

    # 正常控制
    try:
        x_pwm, y_pwm = gimbal.apply_xy(x, y)  # 依你 gimbal.py 的介面
        return jsonify({"locked": False, "goal": False, "x_pwm": x_pwm, "y_pwm": y_pwm})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/center", methods=["POST"])
def api_center():
    """回到中立位置"""
    try:
        gimbal.center()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/goal", methods=["GET"])
def api_goal():
    """手機端輪詢 GOAL 狀態"""
    return jsonify({
        "goal": bool(goal_triggered),
        "goal_time": goal_time
    })


@app.route("/api/reset_goal", methods=["POST"])
def api_reset_goal():
    """如果你想重玩：手動解鎖（可選用）"""
    global goal_triggered, goal_time
    goal_triggered = False
    goal_time = 0.0
    try:
        gimbal.center()
    except Exception:
        pass
    return jsonify({"ok": True})


# =========================
# 收尾清理
# =========================
def cleanup():
    try:
        GPIO.cleanup()
    except Exception:
        pass


atexit.register(cleanup)


if __name__ == "__main__":
    gpio_init()
    t = threading.Thread(target=goal_watcher, daemon=True)
    t.start()

    # 你的 HTTPS 設定若原本就有，請把 ssl_context 改回你自己的
    app.run(host="0.0.0.0", port=8443, debug=False, threaded=True)

