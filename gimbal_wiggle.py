import time
import config
from pca9685_raw import PCA9685Raw

pca = PCA9685Raw(address=config.PCA_ADDR, freq_hz=50)

# 先用「明顯大範圍」測機構（之後再縮小）
X_LEFT  = 240
X_RIGHT = 460
Y_BACK  = 240
Y_FRONT = 460

print("Wiggle test: X then Y. Ctrl+C to stop.")

try:
    while True:
        # X 軸左右擺
        pca.set_pwm_off(config.SERVO_X_CH, X_LEFT)
        time.sleep(0.8)
        pca.set_pwm_off(config.SERVO_X_CH, X_RIGHT)
        time.sleep(0.8)

        # 回中
        pca.set_pwm_off(config.SERVO_X_CH, (X_LEFT + X_RIGHT)//2)
        time.sleep(0.4)

        # Y 軸前後擺
        pca.set_pwm_off(config.SERVO_Y_CH, Y_BACK)
        time.sleep(0.8)
        pca.set_pwm_off(config.SERVO_Y_CH, Y_FRONT)
        time.sleep(0.8)

        # 回中
        pca.set_pwm_off(config.SERVO_Y_CH, (Y_BACK + Y_FRONT)//2)
        time.sleep(0.4)

except KeyboardInterrupt:
    print("\nStopped.")

