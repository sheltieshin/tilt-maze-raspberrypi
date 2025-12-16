import time
import RPi.GPIO as GPIO

BUTTON_PIN = 17
BUZZER_PIN = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, False)

print("按鍵測試中：按下會叫（Ctrl+C 離開）")

try:
    last = GPIO.input(BUTTON_PIN)

    while True:
        now = GPIO.input(BUTTON_PIN)

        # 只在「剛被按下」那一瞬間叫
        if last == 1 and now == 0:
            print("🎯 BUTTON PRESSED")
            GPIO.output(BUZZER_PIN, True)
            time.sleep(0.5)
            GPIO.output(BUZZER_PIN, False)

        last = now
        time.sleep(0.02)

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

