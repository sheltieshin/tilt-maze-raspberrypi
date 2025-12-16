# 🎮 Raspberry Pi 迷宮球專題  
## Web-based Tilt Maze Game using Raspberry Pi and PCA9685

---

**作者**：113453008 張嘉凌 

---

## 一、專題簡介（Project Overview）

本專題實作一套 **以 Raspberry Pi 為核心的 Web 控制實體迷宮球遊戲系統**。  
使用者可透過 **手機瀏覽器（HTTPS）** 操作 **圓形虛擬搖桿介面**，即時控制實體迷宮平台的傾斜角度，讓球體在迷宮中移動並進入目標洞口。

當球成功進洞時，系統會：

- 由 **微動開關** 偵測 GOAL
- 觸發 **蜂鳴器提示**
- 平台自動回到中立位置
- 手機畫面顯示 🎉 GOAL
- 系統自動鎖定，避免誤動
- 提供「再玩一次」機制重新開始

本專題整合 **Web、IoT、嵌入式控制與人機互動設計**，展示從前端到硬體的完整系統實作能力。

---

## 二、系統整體架構（System Architecture）

### 1️⃣ 硬體架構

- Raspberry Pi 4  
- PCA9685（I2C PWM 控制器，Address：`0x40`）  
- SG90 伺服馬達 × 2  
- 雙層雲台結構（Serial Gimbal）  
  - 下層雲台：左右傾斜（X 軸 / Yaw）  
  - 上層雲台：前後傾斜（Y 軸 / Pitch）  
- 微動開關（GOAL 偵測，GPIO17，PUD_UP）  
- 主動蜂鳴器（GPIO22）  
- 外接 5V 伺服電源（共地）

> 本系統採用「兩個單軸雲台上下疊加」的串接式結構，而非傳統雙軸雲台。

---

### 2️⃣ 軟體架構

```text
手機瀏覽器（HTTPS）
        ↓
Flask Web Server（Raspberry Pi）
        ↓
控制 API（/api/tilt）
        ↓
Gimbal 控制模組（gimbal.py）
        ↓
PCA9685 Raw Driver（pca9685_raw.py）
        ↓
SG90 伺服馬達
