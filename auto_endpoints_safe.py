import time
import config
from pca9685_raw import PCA9685Raw

pca = PCA9685Raw(address=config.PCA_ADDR, freq_hz=50)

STEP = 5        # 每一步移動多少 PWM
DELAY = 0.2     # 每一步停多久，方便你看
LOW = 180
HIGH = 560

def move(ch, pwm):
    pwm = max(LOW, min(HIGH, pwm))
    pca.set_pwm_off(ch, pwm)
    return pwm

def find_endpoint(ch, start_pwm, direction, label):
    pwm = start_pwm
    print(f"\n=== 找 {label}（ch{ch}）===")
    print("每次 Enter 會再動一小步")
    print("覺得『快撐住 / 夠斜了』時，輸入 q + Enter 停下")

    while True:
        pwm = move(ch, pwm + direction * STEP)
        print(f"{label} PWM = {pwm}")
        time.sleep(DELAY)

        cmd = input("Enter=繼續 | q=停 > ").strip().lower()
        if cmd == 'q':
            print(f"{label} 定在 {pwm}")
            return pwm

def main():
    x_center = (config.X_MIN + config.X_MAX) // 2
    y_center = (config.Y_MIN + config.Y_MAX) // 2

    print(f"移到中心 X={x_center}, Y={y_center}")
    move(config.SERVO_X_CH, x_center)
    move(config.SERVO_Y_CH, y_center)
    time.sleep(0.5)

    x_max = find_endpoint(config.SERVO_X_CH, x_center, +1, "X_MAX")
    move(config.SERVO_X_CH, x_center)
    time.sleep(0.5)

    x_min = find_endpoint(config.SERVO_X_CH, x_center, -1, "X_MIN")
    move(config.SERVO_X_CH, x_center)
    time.sleep(0.5)

    y_max = find_endpoint(config.SERVO_Y_CH, y_center, +1, "Y_MAX")
    move(config.SERVO_Y_CH, y_center)
    time.sleep(0.5)

    y_min = find_endpoint(config.SERVO_Y_CH, y_center, -1, "Y_MIN")
    move(config.SERVO_Y_CH, y_center)
    time.sleep(0.5)

    print("\n=== 校正完成，請貼回 config.py ===")
    print(f"X_MIN = {x_min}")
    print(f"X_MAX = {x_max}")
    print(f"Y_MIN = {y_min}")
    print(f"Y_MAX = {y_max}")

if __name__ == "__main__":
    main()

