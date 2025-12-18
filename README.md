# 樹莓派 IoT 專題：使用 Python 與 GPIO 製作網頁控制迷宮球
(Web-Controlled Tilt Maze Game with Raspberry Pi)

#### 113453008 張嘉凌
---

## Step 1：專題簡介

以下將示範如何使用 **Raspberry Pi**、**PCA9685**、**Python** 與 **SG90雙軸雲台**，製作一個可透過手機瀏覽器控制的實體迷宮球裝置。

使用者可在手機上操作虛擬搖桿，即時控制平台傾斜方向，讓球滾動至終點。當球進洞時，系統會透過磁簧開關偵測並觸發蜂鳴器提示。

本專題重點在於：

* GPIO 輸入（磁簧開關）
* GPIO 輸出（蜂鳴器）
* I2C 控制 PCA9685 伺服馬達
* Flask 網頁控制

---

## Step 2：準備所需材料

### 硬體

* Raspberry Pi 4
* PCA9685 PWM 伺服控制板
* SG90 伺服馬達（雙軸雲台 ×2 一台控制X軸 一台控制Y軸）
* 磁簧開關（Reed Switch）
* 主動式蜂鳴器
* 外接 5V 電源
* 杜邦線、迷宮平台、支柱、磁鐵球


<img src="https://github.com/user-attachments/assets/4e440140-2720-4e61-b6c5-51014fab969d" width="600" alt="863088_0">


圖 1：整體系統架構，包含 Raspberry Pi、PCA9685、雙雲台傾斜平台與迷宮板。


### 軟體

* Raspberry Pi OS
* Python 3.7
* Flask
* RPi.GPIO

---

## Step 3：GPIO 基本概念說明

GPIO 允許 Raspberry Pi 與外部世界互動。

在本專題中：

* **GPIO17**：作為輸入（磁簧開關）
* **GPIO22**：作為輸出（蜂鳴器）

我使用 **BCM 編號模式**，並搭配 **內建上拉電阻（PUD_UP）**。

---

## Step 4：磁簧開關電路接線（Input）

### 接線方式

| 磁簧開關 | Raspberry Pi |
| ---- | ------------ |
| 一端   | GPIO17       |
| 一端   | GND          |

* 平時 GPIO17 透過上拉電阻為 HIGH（1）
* 磁鐵靠近時，磁簧導通，GPIO17 變為 LOW（0）
* 可避免「懸空腳位」造成不穩定
* 貼在終點下方


<img src="https://github.com/user-attachments/assets/7c017da7-1a25-4f9e-9d11-0f28584bc2f6" width="600" alt="863081_0">


圖 2：磁簧開關

---

## Step 5：蜂鳴器電路接線（Output）

| 蜂鳴器 | Raspberry Pi |
| --- | ------------ |
| 正極  | GPIO22       |
| 負極  | GND          |

本專題使用 **主動式蜂鳴器**，當 GPIO22 設為 HIGH 時即會發聲。


<img src="https://github.com/user-attachments/assets/20bf2360-1c3c-4fe6-a7ac-96fd60debb70" width="600" alt="863116">


圖 3：磁簧開關 & 蜂鳴器


---

## Step 6：測試磁簧開關與蜂鳴器（Python 範例）

以下程式可用來測試 GPIO 是否正確連接：

```python
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
            print("REED SWITCH")
            GPIO.output(BUZZER_PIN, True)
            time.sleep(0.5)
            GPIO.output(BUZZER_PIN, False)

        last = now
        time.sleep(0.02)

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
```

若磁鐵靠近磁簧開關，蜂鳴器應發出聲音。

---

## Step 7：使用 PCA9685 控制伺服馬達

為避免直接使用 GPIO PWM 造成抖動，本專題使用 **PCA9685** 進行 I2C 控制。

### I2C 接線

| PCA9685 | Raspberry Pi |
| ------- | ------------ |
| VCC     | 3.3V         |
| GND     | GND          |
| SDA     | GPIO2        |
| SCL     | GPIO3        |


伺服馬達電源使用外接 5V，並與 Raspberry Pi 共地。

<img src="https://github.com/user-attachments/assets/a6960643-95f0-42c1-9e9c-6cc9edf43d87" width="600" alt="863116">


圖 4：PCA9685 接線


<img src="https://github.com/user-attachments/assets/bcb4f2a6-248f-4fed-9d27-fd297eda8a5e" width="600" alt="863087_0">


圖 5：5V5A電源


---

## Step 8：程式碼說明


### 程式碼結構（Source Code）

```text
.
├── app.py
├── config.py
├── gimbal.py
├── pca9685_raw.py
├── auto_endpoints_safe.py
├── servo_test_ch0.py
├── servo_test_ch2.py
├── static/index.html
└── README.md
```

### 必要安裝套件
- Python 3.7+
- Flask
- RPi.GPIO
- smbus (I2C)

### Install
- sudo apt update
- sudo apt install -y python3-pip python3-rpi.gpio python3-smbus i2c-tools
- pip3 install flask


| 套件       | 用到的程式                                                         |
| -------- | ------------------------------------------------------------- |
| Flask    | `app.py`                                                      |
| RPi.GPIO | `app.py`                                                      |
| smbus    | `pca9685_raw.py`, `auto_endpoints_safe.py`, `servo_test_*.py` |
| 內建模組  | `gimbal.py`, `config.py`                                      |


## Enable I2C (Raspberry Pi)

- 1. 開啟設定工具
```
sudo raspi-config
```
- 2. 進入選單
```
Interface Options
 → I2C
 → Yes
```
- 3. 重新開機
```
sudo reboot
```
- 4.確認 I2C 是否啟用
```
i2cdetect -y 1
```

若看到 40，表示 PCA9685 已被偵測到。

本專案使用 I2C bus 1（Raspberry Pi 預設）

PCA9685 預設位址為 0x40（可由板上 A0–A5 調整）





#### 1. servo_test_ch0.py、servo_test_ch2.py （單通道伺服測試程式）

用途： 最小化測試 PCA9685 CH0 是否能正常輸出 PWM，確認 I2C 與伺服接線是否正常。

僅用於 硬體初期驗證與除錯；正式系統已由 pca9685_raw.py + gimbal.py 取代，不會在主程式中使用。


```
set_pwm(0, 300)
time.sleep(2)
set_pwm(0, 450)

```



#### 2. auto_endpoints_safe.py（伺服端點校正工具 = 只在調機時跑)

用途： 互動式「一小步一小步」移動 SG90（透過 PCA9685），讓你手動找出 X/Y 軸的安全極限位置（X_MIN/X_MAX/Y_MIN/Y_MAX），最後把結果貼回 config.py，避免伺服撐住或超行程。

```
def find_endpoint(ch, start_pwm, direction, label):
    pwm = start_pwm
    while True:
        pwm = move(ch, pwm + direction * STEP)   # 每次推進一小步
        time.sleep(DELAY)
        if input("Enter=繼續 | q=停 > ").strip().lower() == 'q':
            return pwm
```

從中心點開始，按 Enter 逐步增加/減少 PWM，直到覺得「快撐住/夠斜了」輸入 q 停下，回傳該軸端點 PWM。

main() 依序找 X_MAX → X_MIN → Y_MAX → Y_MIN，最後印出校正值，讓我貼回 config.py。



#### 3. config.py（全域硬體與行為設定）

用途： 集中管理伺服端點、通道對應、GPIO 腳位與 Web 服務設定，讓主程式與校正工具共用同一組參數，避免寫死在程式中。

```
SERVO_X_CH = 0
SERVO_Y_CH = 2

# PWM units are 0~4095 at 50Hz, typical usable range for SG90 ~ 150~600
X_CENTER = 380
Y_CENTER = 410

X_MIN, X_CENTER, X_MAX = 180, 380, 500
Y_MIN, Y_CENTER, Y_MAX = 230, 410, 560

# Tilt scaling (web input -1.0 ~ +1.0 maps to endpoints)
# 先小一點，避免抖動/硬撐
X_SCALE = 0.75
Y_SCALE = 0.65

```

定義 PCA9685 位址、伺服通道、X/Y 軸 PWM 端點與中心點，校正完成後只需更新這裡即可影響整個系統。

同時包含 磁簧開關、蜂鳴器 GPIO 與 HTTPS 伺服器設定，作為專案的單一設定來源。




#### 4. gimbal.py（雙軸雲台控制抽象）

用途： 將「前端輸入的 -1.0～+1.0 傾斜值」轉換為安全的 PWM，統一處理中心點、端點限制與縮放，避免直接操作伺服造成抖動或硬撐。

```
def xy_to_pwm(self, v):
    c = self.center()
    if v >= 0:
        pwm = c + v * (self.pwm_max - c) * self.scale
    else:
        pwm = c + v * (c - self.pwm_min) * self.scale
    return self.clamp_pwm(round(pwm))

```

這支會被主程式 app.py 在遊戲運作時呼叫，遊戲中實際控制雲台




#### 5. pca9685_raw.py（PCA9685 Driver）

用途： 本專案使用 **自製的低階 PCA9685 驅動**，不依賴外部第三方套件（如 Adafruit library），直接透過 I2C 操作 PCA9685，設定 PWM 頻率並對指定 channel 輸出 PWM，是所有伺服控制與校正程式的最底層依賴。


```
pca = PCA9685Raw(address=0x40, freq_hz=50)
def set_pwm_off(self, channel, off):
    self.set_pwm(channel, 0, int(off))

```

封裝 PCA9685 的初始化與 PWM 設定（50Hz 適用 SG90），提供最基本的 set_pwm_off() 介面。

被 gimbal.py 與所有 校正程式 共用，屬於專案的 核心底層模組（必用）。




#### 6. app.py（主程式／Web 控制與遊戲邏輯）

用途： 專案的實際執行入口。提供手機端 Web API 控制雲台傾斜，並監聽磁簧開關達成終點後觸發蜂鳴器。



- 初始化雲台控制（PCA9685 + Gimbal）：建立 PCA9685 與雙軸雲台控制物件，載入 config.py 的端點與中心值，啟動時先回中立位置。

```
pca = PCA9685Raw(address=config.PCA_ADDR, freq_hz=50)

servo_x = ServoEndpoint(
    ch=config.SERVO_X_CH,
    pwm_min=config.X_MIN,
    pwm_max=config.X_MAX,
    scale=config.X_SCALE
)
servo_x.pwm_center = config.X_CENTER

servo_y = ServoEndpoint(
    ch=config.SERVO_Y_CH,
    pwm_min=config.Y_MIN,
    pwm_max=config.Y_MAX,
    scale=config.Y_SCALE
)

gimbal = Gimbal(pca, servo_x, servo_y)
gimbal.center()

```



- 磁簧開關監聽（終點偵測）：背景執行緒監聽磁簧開關 1→0 邊緣，球進洞即判定通關、回中立並鳴叫提示。

```
def goal_watcher():
    if (not goal_triggered) and last == 1 and now == 0:
        goal_triggered = True
        gimbal.center()
        beep(0.8)
```



- 蜂鳴器控制（避免重複觸發）：使用 lock 保護蜂鳴器，避免多執行緒同時鳴叫造成異常。

```
def beep(duration=0.8):
    with buzzer_lock:
        GPIO.output(BUZZER_GPIO, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_GPIO, GPIO.LOW)
```



- Web API：雲台傾斜控制（遊戲核心）：接收前端傳來的標準化 X/Y 值，透過 gimbal.py 轉為安全 PWM 控制雙軸雲台；通關後自動鎖定操作。

```
@app.route("/api/tilt", methods=["POST"])
def api_tilt():
    if goal_triggered:
        return jsonify({"locked": True})
    x_pwm, y_pwm = gimbal.set_xy(x, y)
```



- 系統啟動（HTTPS + 背景監聽）：啟動終點監聽執行緒，並以 HTTPS 提供手機端即時控制介面。

```
threading.Thread(target=goal_watcher, daemon=True).start()
app.run(host=config.HOST, port=config.PORT, ssl_context=context)
```


app.py 為整個迷宮球系統的控制核心，整合 Web 控制、雙軸雲台驅動、磁簧終點偵測與蜂鳴回饋，負責實際的遊戲運作流程。


---

## Step 9：機構設計（Mechanical Design）

本專題使用 **雙層雙軸雲台結構**：

* 下層雲台：控制左右傾斜
* 上層雲台：控制前後傾斜
* 平台固定於最上層
* 此設計比四角多馬達平台更容易校正與控制。

<img src="https://github.com/user-attachments/assets/270dde5c-0fcb-43d4-8fdc-0113758b82e8" width="600" alt="863089_0">


圖 6：本專題採用分離式雙雲台配置，一個雲台位於左側中間控制左右傾斜，另一個雲台位於下方中間控制前後傾斜，以簡化結構並提升穩定性。

---

## Step 10：網頁控制介面（Web Control）

本專題使用 Flask 建立 HTTPS 伺服器，提供手機瀏覽器操作介面。

功能包含：

* 圓形虛擬搖桿
* 即時平台控制
* GOAL 狀態顯示
* 過關後自動鎖定


<img src="https://github.com/user-attachments/assets/93620567-0bd4-436e-9799-f2cd071c9f7c" width="400" alt="863126_0">


圖 7: 進入頁面後，雲台平台會維持在「中立水平位置」，圓形搖桿顯示在中心點，代表目前沒有輸入傾斜指令。

- 介面上方提供三個控制按鈕：
- Enable：啟用搖桿控制
- Pause：暫停控制（凍結目前平台角度）
- Center：將平台回復至水平中立位置
- 下方顯示目前 X / Y 的輸入值，以及實際送出的伺服 PWM 訊號。


<img src="https://github.com/user-attachments/assets/ad7eacd6-11c4-4e08-8cdf-242c1f7d3468" width="400" alt="863125_0">


圖 8: 圓形搖桿操作示意（連續傾斜與斜向移動）

- 使用者可拖曳圓形搖桿，連續控制平台的前後（Y 軸）與左右（X 軸）傾斜角度。
- 搖桿支援 斜向（↖ ↗ ↙ ↘）輸入，可同時產生 X 與 Y 的控制值，使球體能夠沿斜向路徑滾動。
- 搖桿移動距離越大，代表傾斜幅度越大；鬆開搖桿後，平台會自動回到中立位置，以避免球體失控。



<img src="https://github.com/user-attachments/assets/22ea079b-a207-4911-af92-7572fac01844" width="400" alt="863131">


圖 9: GOAL 觸發後的系統反應畫面

- 當球體滾入終點並觸發 磁簧開關（Reed Switch） 時，系統會：
- 立即顯示 🎉 GOAL！ 提示視窗，啟動蜂鳴器發出提示音，自動將平台回到中立位置
- 鎖定控制，防止平台繼續晃動，使用者可按下「再玩一次（解鎖）」按鈕，重置狀態並重新開始遊戲。

---




## Step 10：完整系統整合（Final Integration）

系統運作流程如下：
1. 使用者透過手機控制平台
2. PCA9685 驅動伺服馬達傾斜
3. 球滾動至終點
4. 磁簧開關被觸發
5. 蜂鳴器發聲
6. 平台回中立並鎖定


---

## Step 11：示範影片（Demo Video）

YouTube 示範影片： https://youtu.be/YX4nWWXMFIo?si=_V7ajburnaWpJGNI


---

## Step 12：參考資料（References）

* Scott Kildall, *Raspberry Pi: Python scripting the GPIO*
  [https://www.instructables.com/Raspberry-Pi-Python-scripting-the-GPIO/](https://www.instructables.com/Raspberry-Pi-Python-scripting-the-GPIO/)

* ARM Cloud IoT Core Kit Examples
  [https://github.com/ARM-software/Cloud-IoT-Core-Kit-Examples](https://github.com/ARM-software/Cloud-IoT-Core-Kit-Examples)

* PCA9685 Datasheet
  [https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf](https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf)

---

