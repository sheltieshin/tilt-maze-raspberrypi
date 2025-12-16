import time
import RPi.GPIO as GPIO

IR_PIN = 17  # 你接的 OUT

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Read IR only... Ctrl+C to exit")
try:
    while True:
        print("IR =", GPIO.input(IR_PIN))
        time.sleep(0.2)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

