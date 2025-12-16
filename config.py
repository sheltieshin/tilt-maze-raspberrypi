# config.py
# PCA9685 I2C address
PCA_ADDR = 0x40

# Gimbal servos mapping (you confirmed)
SERVO_X_CH = 0   # down左右 (pitch)
SERVO_Y_CH = 2   # up前後 (pitch)

# Servo endpoints (你先用這組，之後用 calibrate_endpoints.py 調整)
# PWM units are 0~4095 at 50Hz, typical usable range for SG90 ~ 150~600
X_CENTER = 380
Y_CENTER = 430

X_MIN = 180
X_MAX = 480
Y_MIN = 190
Y_MAX = 560

# Tilt scaling (web input -1.0 ~ +1.0 maps to endpoints)
# 建議先小一點，避免抖動/硬撐
X_SCALE = 0.55
Y_SCALE = 0.75

# IR sensor GPIO (BCM numbering)
IR_GPIO = 23

# LED + Buzzer GPIO (BCM)
LED_GPIO = 24
BUZZER_GPIO = 25

# IR polarity: None = auto-detect at runtime (recommended)
# True  => triggered when GPIO == 1
# False => triggered when GPIO == 0
IR_ACTIVE_HIGH = None

# HTTPS
HOST = "0.0.0.0"
PORT = 8443
CERT_FILE = "cert/cert.pem"
KEY_FILE = "cert/key.pem"

