# IoT-Based Web-Controlled Tilt Maze System

本專題為一個以 **Raspberry Pi** 為 IoT 終端裝置的互動式控制系統。系統透過 **HTTPS Web 介面** 接收使用者輸入，經由網路傳輸與控制邏輯處理後，驅動實體致動器（伺服馬達）改變迷宮平台傾斜狀態，並結合感測與回饋機制，形成完整的 IoT 控制迴路。

本文件作為本專題的 **Single Source of Truth (SSOT)**，整合系統架構、IoT 設計思維、實作細節與設計演進反思。

#### 作者：張嘉凌 113453008

## 1. 專案概覽

### 1.1 專案目標

本專題的核心目標為：

- 實作一個完整的 **IoT 控制系統流程**
- 將「感測 → 連網 → 控制 → 實體回饋」整合為可重現的系統
- 探討 Web 技術在 IoT 遠端控制中的實務應用
- 驗證在實體環境中，IoT 系統穩定性對整體系統的重要性

### 1.2 系統定位

本系統涵蓋 IoT 課程中的核心：

| IoT 核心層 | 本系統實作 |
|-----------|-----------|
| Sensing（感測） | 磁簧開關（GOAL 偵測） |
| Connectivity（連網） | HTTPS + REST API |
| Processing（處理） | Flask Web Server + 控制邏輯 |
| Actuation（致動） | PCA9685 + 伺服馬達 |
| Feedback（回饋） | 蜂鳴器 + Web UI 狀態 |

---

## 2. 系統架構

### 2.1 IoT 系統流程

```text
User (Mobile Browser)
        ↓ HTTPS
Raspberry Pi (Flask Web Server)
        ↓ REST API
Control Logic (2D Input Mapping)
        ↓
Actuation Layer (PCA9685)
        ↓
Physical Layer (Servo + Platform)
        ↓
Sensing (Micro Switch)
        ↓
Feedback (Buzzer + Web UI)
```

### 2.2 為何使用 HTTPS

本系統採用 **HTTPS** 作為 Web 與 IoT 裝置之間的通訊方式，原因如下：

- 手機瀏覽器的進階互動 API（如部分控制相關事件）
- 僅允許在 **Secure Context（HTTPS）** 下使用
- 符合現代 **IoT Web-based 控制系統** 的安全設計原則

因此，本專題使用 **Flask** 搭配 **自簽憑證**，在 Raspberry Pi 上建立 HTTPS Web Server，確保 Web UI 可正常作為 IoT 控制介面使用。

---

## 3. 硬體與 Physical Layer 設計

### 3.1 Physical Layer 在 IoT 系統中的角色

| Component | GPIO Pin | Description |
|---------|----------|-------------|
| GOAL Switch | GPIO17 | Edge-triggered input (PUD_UP) |
| Buzzer | GPIO22 | Feedback output |
| PCA9685 SDA | GPIO2 | I2C Data |
| PCA9685 SCL | GPIO3 | I2C Clock |
| Servo Power | External 5V | Shared ground with Pi |

在本 IoT 系統中，實體結構屬於 **Physical / Actuation Layer**，其設計目的並非機械效能本身，而是確保：
> **網路控制指令能被穩定、可重現地轉換為物理動作。**

在 IoT 系統中，若 **Physical Layer 不穩定**，上層的 **Connectivity（連網）** 與 **Control Logic（控制邏輯）** 將無法被正確驗證。
因此，本專題將「**結構穩定性**」視為 **IoT 系統可靠性的前提條件**。


### 3.2 致動設計

本系統的致動層設計如下：

- 使用 **PCA9685** 作為 PWM 控制模組
- 控制 **SG90 伺服馬達 × 2**
  - 一顆負責 **左右傾斜（X 軸）**
  - 一顆負責 **前後傾斜（Y 軸）**
- 採用 **Serial Gimbal（串接單軸）** 結構

此設計可有效：

- 降低多軸同步控制的複雜度
- 提升整體控制穩定性

### 3.3 GPIO & Power Wiring Overview
To ensure system reproducibility and physical-layer reliability, this project documents the GPIO, I2C, and power wiring design. - Raspberry Pi acts as the IoT control node. - PCA9685 is used as an external PWM controller via I2C. - Servo motors are powered by an external 5V supply with shared ground. - GPIO-based sensors and feedback devices are directly connected to the Pi. This design follows common IoT hardware integration practices and ensures stable operation of the actuation layer.

---

## 4. 軟體架構與模組分工

### 4.1 專案檔案結構與功能對應

```text
tiltmaze/
├── app.py                  # IoT 主控制節點（HTTPS Web Server + API + GPIO + GOAL事件）
├── config.py               # GPIO / PWM 範圍 / HTTPS 參數（可重現性設定集中管理）
├── gimbal.py               # 2D 控制輸入（x,y）→ 伺服 PWM 映射（含限制/保護）
├── pca9685_raw.py          # PCA9685 I2C Raw Driver（避免外部套件相容性問題）
├── static/
│   └── index.html          # Web UI（圓形虛擬搖桿 + GOAL輪詢 + UI鎖定）
│
├── servo_test_one.py       # 單顆伺服測試（確認硬體/電源/PWM 基本可動）
├── servo_test_ch2.py       # 第二通道伺服測試（多通道驗證）
├── calibrate_endpoints.py  # 伺服校正工具（找出每顆伺服安全PWM範圍與中立點）
├── button_buzzer_test.py   # 感測器/蜂鳴器快速測試（Sense+Feedback單元驗證）
└── ir_read_only.py         # 感測輸入測試（只讀取，不驅動致動器）
```

### 4.2 模組化設計目的

透過模組化設計，本系統達成以下 **IoT 工程目標**：

- 控制邏輯可獨立於硬體測試（先確保 Actuation Layer 可動，再整合 Web/事件）  
- 感測、致動、介面可分別驗證（Sense / Actuation / UI 分段測）
- 提升系統可維護性與可重現性（設定集中在 config.py，避免「同一份程式換一台就壞」）  
- 降低單一模組錯誤對整體系統的影響（driver/映射/UI 任一層出問題可快速定位）  

### 4.3 校正程式的用意

本專題的致動器使用 SG90 伺服馬達，其 PWM 範圍與「中立點」在不同顆伺服上可能存在差異。
若不校正，容易造成以下問題：

平台無法回到真正水平（中立偏移）
伺服撞到極限導致抖動、過熱或卡死（物理層不穩定）
控制輸入相同但輸出動作不一致（無法驗證 IoT 控制效果）
因此，本系統將「校正」視為 IoT 系統可重現性的必要流程。

校正工具：calibrate_endpoints.py

用來找出每顆伺服的：
pwm_min（安全最小值）
pwm_max（安全最大值）
pwm_center（真正水平/中立）

校正完成後，把結果寫回 config.py，成為後續控制的唯一依據（SSOT）。

快速硬體驗證：
servo_test_one.py：先確認「單顆伺服＋供電」是否正常可動
servo_test_ch2.py：確認第二通道或另一顆伺服是否一致可動

IoT 觀點：如果 Physical / Actuation Layer 不可重現，上層 Web 控制與事件機制就無法被正確驗證。

### 4.4 app.py 在做什麼

`app.py` 是整個系統的 **IoT 控制節點（Control Node）**，負責整合
感測（Sense）、致動（Actuation）、網路（Connectivity）與事件控制邏輯，其主要職責如下：

#### Connectivity Layer：HTTPS Web Server
- 提供手機瀏覽器可存取的 **HTTPS 介面（Secure Context）**
- 確保 Web UI 能安全地呼叫 IoT 控制 API

#### Control API：接收控制輸入
- `/api/tilt`：接收前端送來的 `(x, y)` 二維控制量
- 將控制量交由 `gimbal.py` 映射成伺服 PWM
- 再透過 `pca9685_raw.py` 輸出 PWM 訊號驅動伺服馬達

#### Sense & Event Layer：GOAL 偵測
- 透過背景執行緒持續監聽 GOAL 感測器（Edge Trigger）
- 當偵測到 GOAL 時：
  - 設定 `goal_triggered = True`
  - 確保事件只觸發一次，避免抖動或重複觸發

#### Feedback Layer：蜂鳴器與 UI 鎖定
- 當 GOAL 被觸發後，系統會：
  - 觸發蜂鳴器作為回饋提示
  - 將平台回到中立位置（`gimbal.center()`）
  - 使 `/api/tilt` 進入 `locked` 狀態，拒絕後續控制指令
- 前端 Web UI 會透過輪詢 `/api/goal` 顯示 🎉 GOAL overlay

#### Reset / Replay
- `/api/reset_goal`：
  - 清除 GOAL 狀態
  - 解除系統鎖定，允許使用者重新開始遊戲

---

### 4.5 API 規格（Web-based IoT Interface）

| Endpoint | Method | Purpose |
|--------|--------|--------|
| `/api/tilt` | POST | 傳入 `{x, y}` 控制平台傾斜；若 GOAL 已觸發則回傳 `locked` |
| `/api/center` | POST | 平台回中立位置（安全狀態） |
| `/api/goal` | GET | 回傳 GOAL 狀態（供前端輪詢） |
| `/api/reset_goal` | POST | 清除 GOAL 鎖定，允許再次控制 |

---

### 4.6 測試策略（Unit → Integration）

為降低系統整合風險，本專題採用 **由下而上（Bottom-up）** 的逐層測試策略：

#### Actuation 單元測試
- `servo_test_one.py`
- `servo_test_ch2.py`
- 確認單顆與多通道伺服在獨立狀態下可正常運作

#### Calibration 校正
- `calibrate_endpoints.py`
- 校正伺服 PWM 安全範圍與中立點，並更新至 `config.py`

#### Sense / Feedback 單元測試
- `button_buzzer_test.py`
- 確認感測輸入與蜂鳴器回饋可獨立正常運作

#### 整合測試（End-to-End）
- 啟動 `app.py`
- 使用手機瀏覽器開啟  
  `https://<raspberry-pi-ip>:8443`
- 實際操作 Web UI，觀察平台控制與 GOAL 事件是否符合預期


---

## 5. 設計演進與工程取捨

### 5.1 初期構想與問題

專題初期嘗試使用 **手機陀螺儀** 作為控制輸入來源，但在實作過程中發現以下問題：

- 陀螺儀屬於 **三維感測（Pitch / Roll / Yaw）**  
- 迷宮控制實際僅需 **二維傾斜**  
- 多餘維度導致輸入雜訊與方向干擾  
- 控制結果難以預測與重現  


### 5.2 控制方式的修正

為提升控制穩定性與可預測性，最終改採 **Web 圓形虛擬搖桿（2D操控UI）**：

- 明確限制輸入維度為 **2D**  
- 降低感測雜訊影響  
- 提升 IoT 控制效果的一致性  
- 更適合遠端 **Web-based IoT 控制情境**  


### 5.3 致動結構的取捨

曾評估使用「**四角雙軸雲台（共 8 顆伺服）**」方案，但實作後發現：

- 伺服校正成本極高  
- 摩擦力與推點不一致  
- 同步控制誤差累積  
- 控制邏輯複雜度顯著上升  

最終選擇 **雙伺服 + 被動支點** 架構：

- 減少致動器數量  
- 提升整體穩定性  
- 使 IoT 控制結果 **可被重現與驗證**  

---

## 6. GOAL 感測與回饋機制

### 6.1 感測與事件觸發

- 使用 **微動開關** 作為事件感測器（GPIO）  
- 透過 **背景執行緒** 偵測 Edge Trigger  
- 避免誤觸與重複觸發  


### 6.2 事件發生後系統行為

當 **GOAL** 被觸發時，系統將：

- 平台回到中立位置  
- 蜂鳴器發出提示音  
- Web UI 顯示完成狀態  
- 系統進入鎖定模式，防止誤操作  


### 6.3 感測器選型與安裝設計

為了在迷宮球掉入終點（GOAL）時，能穩定且可重現地觸發完成事件，
本系統採用「磁力球 + 裸磁簧開關（Reed Switch）」作為終點感測方案。

#### 設計方式說明

- 在迷宮終點洞口下方設置一個小型接收杯
- 當磁力球掉入杯中時，磁場接近杯外側的磁簧開關
- 磁簧開關狀態改變，透過 GPIO Edge Detection 觸發系統事件

此設計具備以下優點：

- **非接觸式感測**：不需依賴球體重量或撞擊力
- **高靈敏度**：即使輕量鋼珠亦可穩定觸發
- **結構整合性高**：磁簧可隱藏於杯體外側，不影響迷宮表面
- **事件可重現性高**：適合作為 IoT 系統中的 Sense Layer 節點

#### 為何不採用其他感測方案

在設計過程中，曾測試過以下替代方案，但最終未採用：

- **微動開關**  
  球體重量不足以穩定按壓開關，導致誤判或無法觸發。

- **紅外線槽型光耦**  
  雖具備高靈敏度，但對安裝精度與環境光線較為敏感，
  且在本迷宮結構中較難

---

## 7. 系統啟動與測試

啟動主程式：

```bash
python3 app.py
```
使用手機瀏覽器開啟：

```bash
https://<raspberry-pi-ip>:8443
```

---

## 8. 限制與未來展望

### 已知限制

- 伺服馬達扭力有限，平台尺寸與重量需受限  
- 使用自簽憑證，非正式 CA  
- 目前僅支援單一使用者操作模式  

### 未來展望

- 支援多裝置同時連線與控制
- 增加迷宮難度與遊戲模式（計時、關卡制）  
- 將操作行為與結果上傳雲端進行資料分析與視覺化  

---

## 9. 總結

本專題強調：

> **在 IoT 系統中，唯有 Physical Layer 穩定，  
> 上層的連網與控制邏輯才具有驗證意義。**

透過多次設計修正，本系統成功實作一個：

- 可感測（Sense）  
- 可連網（Connectivity）  
- 可控制（Actuation）  
- 可回饋（Feedback）  
- 可重現（Reproducibility）  

的 **完整 IoT 系統實作案例**。

