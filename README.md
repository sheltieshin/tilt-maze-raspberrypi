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

### 軟體

* Raspberry Pi OS
* Python 3.7
* Flask
* RPi.GPIO

![863089_0](https://github.com/user-attachments/assets/270dde5c-0fcb-43d4-8fdc-0113758b82e8)


---

## Step 3：GPIO 基本概念說明

GPIO（General Purpose Input/Output）允許 Raspberry Pi 與外部世界互動。

在本專題中：

* **GPIO17**：作為輸入（磁簧開關）
* **GPIO22**：作為輸出（蜂鳴器）

我們使用 **BCM 編號模式**，並搭配 **內建上拉電阻（PUD_UP）**。

---

## Step 4：磁簧開關電路接線（Input）

### 接線方式

| 磁簧開關 | Raspberry Pi |
| ---- | ------------ |
| 一端   | GPIO17       |
| 一端   | GND          |

📌 原理說明：

* 平時 GPIO17 透過上拉電阻為 HIGH（1）
* 磁鐵靠近時，磁簧導通，GPIO17 變為 LOW（0）
* 可避免「懸空腳位」造成不穩定

📷（此處可放接線圖或麵包板圖）

---

## Step 5：蜂鳴器電路接線（Output）

| 蜂鳴器 | Raspberry Pi |
| --- | ------------ |
| 正極  | GPIO22       |
| 負極  | GND          |

本專題使用 **主動式蜂鳴器**，當 GPIO22 設為 HIGH 時即會發聲。

---

## Step 6：測試磁簧開關與蜂鳴器（Python 範例）

以下程式可用來測試 GPIO 是否正確連接：

```python
import time
import RPi.GPIO as GPIO

REED_GPIO = 17
BUZZER_GPIO = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(REED_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_GPIO, GPIO.OUT)
GPIO.output(BUZZER_GPIO, False)

print("磁簧測試中（Ctrl+C 離開）")

try:
    last = GPIO.input(REED_GPIO)
    while True:
        now = GPIO.input(REED_GPIO)
        if last == 1 and now == 0:
            print("GOAL!")
            GPIO.output(BUZZER_GPIO, True)
            time.sleep(0.5)
            GPIO.output(BUZZER_GPIO, False)
        last = now
        time.sleep(0.02)
finally:
    GPIO.cleanup()
```

📌 若磁鐵靠近磁簧開關，蜂鳴器應發出聲音。

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

---

## Step 8：機構設計（Mechanical Design）

本專題使用 **雙層雙軸雲台結構**：

* 下層雲台：控制左右傾斜
* 上層雲台：控制前後傾斜
* 平台固定於最上層

📌 此設計比四角多馬達平台更容易校正與控制。

📷（此處可放雲台照片）

---

## Step 9：網頁控制介面（Web Control）

本專題使用 Flask 建立 HTTPS 伺服器，提供手機瀏覽器操作介面。

功能包含：

* 圓形虛擬搖桿
* 即時平台控制
* GOAL 狀態顯示
* 過關後自動鎖定

---

## Step 10：完整系統整合（Final Integration）

當系統運作流程如下：

1. 使用者透過手機控制平台
2. PCA9685 驅動伺服馬達傾斜
3. 球滾動至終點
4. 磁簧開關被觸發
5. 蜂鳴器發聲
6. 平台回中立並鎖定

---

## Step 11：示範影片（Demo Video）

🎥 YouTube 示範影片：
👉（請貼上你的影片連結）

---

## Step 12：程式碼結構（Source Code）

```text
.
├── app.py
├── config.py
├── gimbal.py
├── pca9685_raw.py
├── static/index.html
└── README.md
```

---

## Step 13：參考資料（References）

* Scott Kildall, *Raspberry Pi: Python scripting the GPIO*
  [https://www.instructables.com/Raspberry-Pi-Python-scripting-the-GPIO/](https://www.instructables.com/Raspberry-Pi-Python-scripting-the-GPIO/)

* ARM Cloud IoT Core Kit Examples
  [https://github.com/ARM-software/Cloud-IoT-Core-Kit-Examples](https://github.com/ARM-software/Cloud-IoT-Core-Kit-Examples)

* PCA9685 Datasheet
  [https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf](https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf)

---

## Step 14：結語（Conclusion）

透過本專題，我們成功將 GPIO、伺服控制與網頁介面整合成一個完整的 IoT 裝置，並實際解決了感測器誤判、伺服抖動與平台穩定性等問題。

---

你現在已經不是在趕作業，是在**把一個成熟專題包裝成教學作品**了。
