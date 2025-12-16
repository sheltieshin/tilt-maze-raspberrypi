from dataclasses import dataclass

@dataclass
class ServoEndpoint:
    ch: int
    pwm_min: int
    pwm_max: int
    scale: float = 1.0
    pwm_center = None   # ← Python 3.7 相容寫法

    def center(self):
        # 若有指定中心點，優先使用
        if self.pwm_center is not None:
            return int(self.pwm_center)
        return (self.pwm_min + self.pwm_max) // 2

    def clamp_pwm(self, pwm):
        return max(self.pwm_min, min(self.pwm_max, int(pwm)))

    def xy_to_pwm(self, v):
        """
        v: -1.0 ~ +1.0
        """
        # 保護
        if v > 1.0:
            v = 1.0
        elif v < -1.0:
            v = -1.0

        c = self.center()

        # 以「自訂中心」為基準往兩側推
        if v >= 0:
            pwm = c + v * (self.pwm_max - c) * self.scale
        else:
            pwm = c + v * (c - self.pwm_min) * self.scale

        return self.clamp_pwm(round(pwm))


class Gimbal:
    def __init__(self, pca, servo_x: ServoEndpoint, servo_y: ServoEndpoint):
        self.pca = pca
        self.servo_x = servo_x
        self.servo_y = servo_y

    def set_xy(self, x, y):
        pwm_x = self.servo_x.xy_to_pwm(x)
        pwm_y = self.servo_y.xy_to_pwm(y)
        self.pca.set_pwm_off(self.servo_x.ch, pwm_x)
        self.pca.set_pwm_off(self.servo_y.ch, pwm_y)
        return pwm_x, pwm_y

    def center(self):
        pwm_x = self.servo_x.center()
        pwm_y = self.servo_y.center()
        self.pca.set_pwm_off(self.servo_x.ch, pwm_x)
        self.pca.set_pwm_off(self.servo_y.ch, pwm_y)
        return pwm_x, pwm_y

