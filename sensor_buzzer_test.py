import time
import RPi.GPIO as GPIO

REED_GPIO = 17
BUZZER_PIN = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(REED_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, False)

print("beep...（Ctrl+C 離開）")

try:
    last = GPIO.input(REED_GPIO)

    while True:
        now = GPIO.input(REED_GPIO)

        # 只在「剛被按下」那一瞬間叫
        if last == 1 and now == 0:
            print("🎯 REED SWITCH")
            GPIO.output(BUZZER_PIN, True)
            time.sleep(0.5)
            GPIO.output(BUZZER_PIN, False)

        last = now
        time.sleep(0.02)

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

