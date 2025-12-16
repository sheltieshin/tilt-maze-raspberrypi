import time
import RPi.GPIO as GPIO

# ====== 腳位設定（BCM 編號）======
IR_PIN = 17       # 紅外線 OUT
BUZZER_PIN = 22   # 蜂鳴器 +

# ====== GPIO 初始化 ======
GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

GPIO.output(BUZZER_PIN, False)

print("IR → Buzzer 測試中")
print("遮住紅外線看看蜂鳴器是否會叫（Ctrl+C 離開）")

try:
    last_state = GPIO.input(IR_PIN)

    while True:
        state = GPIO.input(IR_PIN)

        # 狀態變化時印出來（方便你觀察）
        if state != last_state:
            print("IR state =", state)
            last_state = state

        # 👉 常見情況：遮住時 = 0（LOW）
        if state == 0:
            print("🎯 觸發！蜂鳴器叫")
            GPIO.output(BUZZER_PIN, True)
            time.sleep(1.0)
            GPIO.output(BUZZER_PIN, False)
            time.sleep(0.6)  # 防止連續狂叫

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n結束測試")

finally:
    GPIO.cleanup()

