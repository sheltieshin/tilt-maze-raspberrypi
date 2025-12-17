# 🌐 IoT-Based Web-Controlled Tilt Maze System

本專題為一個以 **Raspberry Pi** 為 IoT 終端裝置（IoT End Device）的互動式控制系統。  
系統透過 **HTTPS Web 介面** 接收使用者輸入，經由網路傳輸與控制邏輯處理後，  
驅動實體致動器（伺服馬達）改變迷宮平台傾斜狀態，  
並結合感測與回饋機制，形成完整的 IoT 控制迴路。

本文件作為本專題的 **Single Source of Truth (SSOT)**，  
整合系統架構、IoT 設計思維、實作細節與設計演進反思。

## 作者：張嘉凌 113453008 ##
-

## 1. 專案概覽（Project Overview）

### 1.1 專案目標

本專題的核心目標為：

- 實作一個完整的 **IoT 控制系統流程**
- 將「感測 → 連網 → 控制 → 實體回饋」整合為可重現的系統
- 探討 Web 技術在 IoT 遠端控制中的實務應用
- 驗證在實體環境中，IoT 系統穩定性對整體系統的重要性

### 1.2 系統定位（IoT 課程對齊）

本系統涵蓋 IoT 課程中的主要評分核心：

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
