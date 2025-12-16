# calibrate_endpoints.py
import sys
import termios
import tty
import time

import config
from pca9685_raw import PCA9685Raw

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def main():
    pca = PCA9685Raw(address=config.PCA_ADDR, freq_hz=50)

    x = (config.X_MIN + config.X_MAX) // 2
    y = (config.Y_MIN + config.Y_MAX) // 2

    step_small = 2
    step_big = 10

    print("\n=== Endpoint Calibration (PCA9685 raw) ===")
    print("Keys:")
    print("  a/d : X -/+  (small)")
    print("  A/D : X -/+  (big)")
    print("  w/s : Y -/+  (small)")
    print("  W/S : Y -/+  (big)")
    print("  c   : center both")
    print("  q   : quit (print final PWM)")
    print("\nStart at CENTER. Adjust until tilt looks right and servo not straining.\n")

    while True:
        pca.set_pwm_off(config.SERVO_X_CH, x)
        pca.set_pwm_off(config.SERVO_Y_CH, y)

        sys.stdout.write(f"\rX(ch{config.SERVO_X_CH})={x:4d}  Y(ch{config.SERVO_Y_CH})={y:4d}   ")
        sys.stdout.flush()

        ch = getch()
        if ch == 'q':
            break
        elif ch == 'c':
            x = (config.X_MIN + config.X_MAX) // 2
            y = (config.Y_MIN + config.Y_MAX) // 2
        elif ch == 'a':
            x -= step_small
        elif ch == 'd':
            x += step_small
        elif ch == 'A':
            x -= step_big
        elif ch == 'D':
            x += step_big
        elif ch == 'w':
            y += step_small
        elif ch == 's':
            y -= step_small
        elif ch == 'W':
            y += step_big
        elif ch == 'S':
            y -= step_big

        x = clamp(x, 100, 650)
        y = clamp(y, 100, 650)

        time.sleep(0.01)

    print("\n\nFinal:")
    print(f"  X PWM = {x}")
    print(f"  Y PWM = {y}")
    print("請把你量到的 X_MIN/X_MAX/Y_MIN/Y_MAX 寫回 config.py")
    print("做法：把 X 調到最左(或最右)不硬撐的位置當 MIN/MAX；Y 同理。")

if __name__ == "__main__":
    main()

