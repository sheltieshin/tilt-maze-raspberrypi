# 🌐 IoT-Based Web-Controlled Tilt Maze System

本專題為一個以 **Raspberry Pi** 為 IoT 終端裝置（IoT End Device）的互動式控制系統。系統透過 **HTTPS Web 介面** 接收使用者輸入，經由網路傳輸與控制邏輯處理後，驅動實體致動器（伺服馬達）改變迷宮平台傾斜狀態，並結合感測與回饋機制，形成完整的 IoT 控制迴路。

本文件作為本專題的 **Single Source of Truth (SSOT)**，整合系統架構、IoT 設計思維、實作細節與設計演進反思。

#### 作者：張嘉凌 113453008

## 1. 專案概覽（Project Overview）

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
| Sensing（感測） | 微動開關（GOAL 偵測） |
| Connectivity（連網） | HTTPS + REST API |
| Processing（處理） | Flask Web Server + 控制邏輯 |
| Actuation（致動） | PCA9685 + 伺服馬達 |
| Feedback（回饋） | 蜂鳴器 + Web UI 狀態 |

---

## 2. 系統架構（System Architecture）

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

### 2.2 為何使用 HTTPS（Why HTTPS is Required）

本系統採用 **HTTPS** 作為 Web 與 IoT 裝置之間的通訊方式，原因如下：

- 手機瀏覽器的進階互動 API（如部分控制相關事件）
- 僅允許在 **Secure Context（HTTPS）** 下使用
- 符合現代 **IoT Web-based 控制系統** 的安全設計原則

因此，本專題使用 **Flask** 搭配 **自簽憑證（Self-signed Certificate）**，在 Raspberry Pi 上建立 HTTPS Web Server，確保 Web UI 可正常作為 IoT 控制介面使用。

---

## 3. 硬體與 Physical Layer 設計（IoT 視角）

### 3.1 Physical Layer 在 IoT 系統中的角色

在本 IoT 系統中，實體結構屬於 **Physical / Actuation Layer**，其設計目的並非機械效能本身，而是確保：
> **網路控制指令能被穩定、可重現地轉換為物理動作。**

在 IoT 系統中，若 **Physical Layer 不穩定**，上層的 **Connectivity（連網）** 與 **Control Logic（控制邏輯）** 將無法被正確驗證。
因此，本專題將「**結構穩定性**」視為 **IoT 系統可靠性的前提條件**。

---

### 3.2 致動設計（Actuation Layer）

本系統的致動層設計如下：

- 使用 **PCA9685** 作為 PWM 控制模組
- 控制 **SG90 伺服馬達 × 2**
  - 一顆負責 **左右傾斜（X 軸）**
  - 一顆負責 **前後傾斜（Y 軸）**
- 採用 **Serial Gimbal（串接單軸）** 結構

此設計可有效：

- 降低多軸同步控制的複雜度
- 提升整體控制穩定性

## 4. 軟體架構與模組分工（Software Architecture）

### 4.1 專案檔案結構與功能對應

```text
tiltmaze/
├── app.py                  # IoT 主控制節點（Web Server + API + GPIO）
├── config.py               # GPIO / PWM / HTTPS 設定
├── gimbal.py               # 2D 控制輸入 → 伺服輸出映射
├── pca9685_raw.py          # PCA9685 I2C Raw Driver
├── static/
│   └── index.html          # Web UI（圓形虛擬搖桿）
│
├── servo_test_one.py       # 單顆伺服測試
├── servo_test_ch2.py       # 第二通道伺服測試
├── calibrate_endpoints.py  # 伺服校正工具
├── button_buzzer_test.py   # 感測與蜂鳴器測試
└── ir_read_only.py         # 感測輸入測試

### 4.2 模組化設計目的（IoT Design Rationale）

透過模組化設計，本系統達成以下 **IoT 工程目標**：

- 控制邏輯可獨立於硬體測試  
- 感測、致動、介面可分別驗證  
- 提升系統可維護性與可重現性  
- 降低單一模組錯誤對整體系統的影響  

---

## 5. 設計演進與工程取捨（Design Iteration & Reflection）

### 5.1 初期構想與問題

專題初期嘗試使用 **手機陀螺儀（Gyroscope）** 作為控制輸入來源，  
但在實作過程中發現以下問題：

- 陀螺儀屬於 **三維感測（Pitch / Roll / Yaw）**  
- 迷宮控制實際僅需 **二維傾斜**  
- 多餘維度導致輸入雜訊與方向干擾  
- 控制結果難以預測與重現  

---

### 5.2 控制方式的修正（IoT 視角）

為提升控制穩定性與可預測性，最終改採 **Web 圓形虛擬搖桿（2D Control UI）**：

- 明確限制輸入維度為 **2D**  
- 降低感測雜訊影響  
- 提升 IoT 控制效果的一致性  
- 更適合遠端 **Web-based IoT 控制情境**  

---

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

## 6. GOAL 感測與回饋機制（Sense & Feedback）

### 6.1 感測與事件觸發

- 使用 **微動開關** 作為事件感測器（GPIO）  
- 透過 **背景執行緒** 偵測 Edge Trigger  
- 避免誤觸與重複觸發  

---

### 6.2 事件發生後系統行為

當 **GOAL** 被觸發時，系統將：

- 平台回到中立位置  
- 蜂鳴器發出提示音  
- Web UI 顯示完成狀態  
- 系統進入鎖定模式，防止誤操作  

---

## 7. 系統啟動與測試（Deployment & Testing）

啟動主程式：

```bash
python3 app.py

使用手機瀏覽器開啟：

```bash
https://<raspberry-pi-ip>:8443

## 8. 限制與未來展望（Limitations & Future Work）

### 已知限制

- 伺服馬達扭力有限，平台尺寸與重量需受限  
- 使用自簽憑證（Self-signed Certificate），非正式 CA  
- 目前僅支援單一使用者操作模式  

### 未來展望

- 支援多裝置同時連線與控制（Multi-client IoT Control）  
- 增加迷宮難度與遊戲模式（計時、關卡制）  
- 將操作行為與結果上傳雲端進行資料分析與視覺化  

---

## 9. 總結（IoT 課程對齊）

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

