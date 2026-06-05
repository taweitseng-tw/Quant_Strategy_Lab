# Quant Strategy Lab PRD v0.1

> 文件版本：v0.1  
> 文件類型：Product Requirements Document / 產品需求規格書  
> 專案名稱：Quant Strategy Lab  
> 主要用途：本地端桌面型量化交易策略生成、回測、驗證、篩選與報告平台  
> 主要開發模式：單人主導 + 多模型協作開發  
> 主要模型分工：Anti-Gravity 初階工程、DeepSeek V4 Pro 主力工程、Codex 高階複核與任務分派  

---

## 1. 文件目的

本文件用於定義 **Quant Strategy Lab** 從 0 到 1 的產品定位、功能範圍、技術架構、資料流程、策略生成流程、回測流程、防過度擬合流程、UI/UX 設計、資料庫初稿、開發里程碑、測試計畫與三模型協作規則。

本 PRD 的主要用途：

1. 作為 Codex 建立專案、拆分任務、審查架構的總藍圖。
2. 作為 Anti-Gravity 建立初步工程骨架與 UI 雛形的依據。
3. 作為 DeepSeek V4 Pro 設計演算法、回測核心、防擬合邏輯與效能優化的依據。
4. 作為使用者本人後續管理專案進度、驗收功能、避免範圍失控的依據。

---

## 2. 產品名稱

### 2.1 暫定名稱

**Quant Strategy Lab**

### 2.2 命名理由

此名稱強調「量化策略研究實驗室」的定位，而不是單純看盤軟體、交易平台或自動下單系統。

它的核心不是直接承諾實盤獲利，而是建立一個可視化、可重現、可驗證、可篩選的策略研究流程。

---

## 3. 產品定位

Quant Strategy Lab 是一套 **本地端桌面型量化交易策略生成、回測、驗證、篩選與報告平台**。

它參考 StrategyQuant、AdapTrade Builder、Build Alpha 等軟體的部分概念，但第一版不追求完整複製商業級策略生成平台，而是先建立一條單人可開發、可測試、可逐步擴充的核心研究流水線。

### 3.1 核心研究流水線

```text
資料匯入
→ 資料標準化
→ 週期轉換
→ 商品設定
→ Session 過濾
→ 策略生成
→ 回測
→ IS / Validation / OOS 驗證
→ 壓力測試
→ Monte Carlo
→ Walk-forward
→ 策略排名
→ 視覺化報告
→ 策略保存 / 匯出
```

### 3.2 產品核心精神

本產品不是「漂亮回測製造機」，而是：

```text
策略生成器
+ 回測器
+ 防過度擬合驗證器
+ 垃圾策略淘汰器
+ 候選策略篩選器
+ 可視化策略研究平台
```

### 3.3 第一版產品重點

第一版最重要的是跑通端到端流程：

```text
匯入資料
→ 產生策略
→ 回測
→ OOS 驗證
→ 壓力測試
→ 排名
→ 視覺化
→ 報告匯出
```

而不是一開始就追求完整 Genetic Programming、實盤交易、券商 API、雲端 SaaS、多使用者權限或高頻 Tick 級撮合。

---

## 4. 目標使用者

### 4.1 主要使用者

目前主要使用者為專案擁有者本人。

使用者特徵：

1. 熟悉 Python 中階開發。
2. 有 PyQt5 / 桌面 GUI 開發經驗。
3. 有量化交易與短線策略研究經驗。
4. 曾使用 AdapTrade Builder，熟悉其策略生成與測試流程。
5. 希望透過 Codex、DeepSeek V4 Pro、Gemini / Anti-Gravity 等大型模型協助開發。
6. 希望看到完整視覺化，而不是只有 CLI 或 Notebook 結果。

### 4.2 未來可能使用者

未來可擴展給：

1. 期貨 / 指數策略研究者。
2. 熟悉 MultiCharts / TradeStation 的系統交易者。
3. 需要策略生成與防擬合測試的個人量化交易者。
4. 具備一定程式能力，但不想從零手寫完整策略生成平台的人。

---

## 5. 核心痛點

### 5.1 手動設計策略效率低

傳統策略研發需要人工提出假設、寫程式、回測、調整、再測試。對於大量策略構想，效率很低。

### 5.2 一般回測平台不會自動生成策略

TradeStation、MultiCharts、AmiBroker、QuantConnect 等工具通常強在回測、下單、圖表與腳本，但不一定能自動生成策略邏輯。

### 5.3 自動生成策略容易過度擬合

自動化策略生成器若缺少嚴格 OOS、壓力測試、滑價、手續費、Monte Carlo、Walk-forward，很容易產生漂亮但無法實盤存活的策略。

### 5.4 漂亮權益曲線不代表策略可靠

策略需要經過：

1. Out-of-Sample。
2. 參數擾動。
3. 滑價加倍。
4. 手續費加倍。
5. 隨機漏單。
6. Walk-forward。
7. 多商品交叉驗證。

才能有較高可信度。

### 5.5 現有商業工具不一定符合個人工作流

使用者希望針對自己的研究流程、資料來源、視覺化習慣與 AI 開發流程，建立一套可控、可擴充、可審查的本地工具。

---

## 6. 非目標範圍

MVP v0.1 不做以下功能：

1. 實盤下單。
2. 券商 API 串接。
3. 高頻 Tick 級撮合。
4. 雲端 SaaS。
5. 多人帳號 / 權限系統。
6. 完整 Genetic Programming。
7. 完整 Walk-forward Matrix。
8. 期貨換月自動處理。
9. PDF 報告美化。
10. 完整 Python / NinjaTrader / EasyLanguage 可執行策略碼匯出。
11. 多商品投組級資金配置。
12. 複雜 position sizing。
13. GPU / 分散式運算。
14. 交易所即時行情串接。
15. 自動部署或自動交易監控。

### 6.1 MVP 不做實盤下單的理由

實盤下單會引入：

1. 券商 API。
2. 委託狀態同步。
3. 錯單處理。
4. 斷線處理。
5. 即時風控。
6. 資金控管。
7. 交易責任風險。

這些會大幅拖慢 MVP，因此第一版只做研究與回測。

### 6.2 MVP 不做完整 GP 的理由

Genetic Programming 樹狀結構會大幅提高：

1. 策略定義複雜度。
2. 條件解析難度。
3. 策略可讀性問題。
4. 除錯成本。
5. 回測效能壓力。
6. UI 設計難度。

因此 MVP 先使用固定四區塊策略框架。

---

## 7. MVP 範圍

MVP v0.1 必須完成以下能力。

### 7.1 桌面程式

1. 使用 PySide6 建立桌面主程式。
2. 具備主視窗、左側導航、主要工作區、底部 log panel。
3. 支援建立 / 開啟專案資料夾。
4. 支援基本設定儲存。

### 7.2 專案儲存

1. 每個專案一個資料夾。
2. 每個專案一個 SQLite 資料庫。
3. 大型資料檔可另存 CSV / Parquet。
4. 策略、任務、報告、測試結果寫入 SQLite。
5. 原始資料可選擇複製進專案或只記錄路徑。

### 7.3 資料匯入與處理

1. 優先支援 MultiCharts / TradeStation 類 OHLCV 匯出格式。
2. 支援內部標準 OHLCV schema。
3. 支援 1 分 K resample 成 5 分、15 分、60 分。
4. 支援基本資料品質檢查。
5. 支援基本 session filter。
6. 支援商品 profile。

### 7.4 策略生成

1. 固定四區塊策略架構：
   - Long Entry
   - Long Exit
   - Short Entry
   - Short Exit
2. 支援多空鏡像 / 多空不對稱可選。
3. 支援隨機條件組合。
4. 支援隨機參數。
5. 支援 AND / OR 條件組合。
6. 支援基本指標與價格條件。
7. 支援策略生成停止條件。
8. 支援策略保存。

### 7.5 回測

1. 單商品事件驅動回測。
2. 同時間只持有一個部位。
3. 支援多空方向。
4. 支援 Market Order。
5. 支援 Stop Loss。
6. 支援 Take Profit。
7. 支援持有 N 根 K 棒出場。
8. 支援 session 結束出場。
9. 支援 Open / Close / Next Open 成交假設。
10. 支援手續費與滑價。

### 7.6 驗證與防過度擬合

1. IS / Validation / OOS 切分。
2. OOS 通過規則。
3. 手續費加倍壓力測試。
4. 滑價加倍壓力測試。
5. 參數擾動測試。
6. 隨機漏單測試。
7. 交易延遲一根 K 測試。
8. 基礎 Monte Carlo：
   - 隨機漏單。
   - 隨機滑價擾動。
9. 基礎 Walk-forward。

### 7.7 視覺化

1. OHLCV 表格。
2. K 線預覽。
3. 策略排行榜。
4. Equity Curve。
5. Drawdown Curve。
6. IS / OOS 分色。
7. 交易進出場點位。
8. 壓力測試前後對比圖。
9. Monte Carlo 摘要。
10. Walk-forward 摘要。
11. 策略參數摘要。
12. 交易明細表。

### 7.8 匯出

MVP 支援：

1. Excel 報告。
2. HTML 報告。
3. Markdown 報告。
4. 策略 JSON。
5. Pseudo Code。

MVP 延後：

1. PDF 報告。
2. 完整 Python 策略碼。
3. NinjaTrader 策略碼。
4. EasyLanguage 策略碼。

---

## 8. 產品功能模組

### 8.1 Data Engine

負責資料匯入、標準化、週期轉換、session 過濾、商品設定與資料品質檢查。

#### 8.1.1 Importer

功能：

1. 匯入 MultiCharts / TradeStation 類資料。
2. 匯入 CSV。
3. 匯入 Excel。
4. 未來支援欄位 mapping wizard。

MVP 優先：

```text
MultiCharts / TradeStation 類 OHLCV 匯出資料
```

#### 8.1.2 Schema Normalizer

將不同來源資料轉換成內部標準欄位：

```text
datetime
open
high
low
close
volume
```

可擴充欄位：

```text
symbol
session
open_interest
bid
ask
source
```

#### 8.1.3 Time Parser

功能：

1. 解析 datetime 欄位。
2. 支援日期欄與時間欄分開。
3. 檢查時間排序。
4. 檢查重複時間。
5. 檢查缺漏時間。

MVP 可先支援常見格式，複雜時區處理延後。

#### 8.1.4 Resampler

功能：

1. 由 1 分 K 轉換為 5 分 K。
2. 由 1 分 K 轉換為 15 分 K。
3. 由 1 分 K 轉換為 60 分 K。
4. 未來支援日 K、週 K、自訂週期。

OHLCV resample 規則：

```text
open   = 第一根 open
high   = 區間最高 high
low    = 區間最低 low
close  = 最後一根 close
volume = 區間 volume 加總
```

#### 8.1.5 Session Filter

功能：

1. 支援日盤。
2. 支援夜盤。
3. 支援自訂 session template。
4. 支援 session 結束強制出場。

MVP：

1. 基本 session 過濾。
2. 日盤 / 夜盤可設定。

Alpha：

1. 完整 session template 管理。

#### 8.1.6 Instrument Profile Manager

商品設定檔包含：

```text
symbol
name
market
tick_size
point_value
commission_type
commission_value
slippage_type
slippage_value
currency
session_template
default_position_size
```

用途：

1. 計算點數損益。
2. 計算金額損益。
3. 計算手續費。
4. 計算滑價。
5. 管理交易時段。

#### 8.1.7 Data Quality Checker

檢查項目：

1. 缺值。
2. 重複 datetime。
3. 時間未排序。
4. OHLC 不合理。
5. high < low。
6. open / close 超出 high-low。
7. volume 為負。
8. 大幅跳價。
9. session 外資料。

---

## 9. Strategy Engine

### 9.1 策略架構

MVP 採固定四區塊策略框架：

```text
Long Entry
Long Exit
Short Entry
Short Exit
```

每一區塊可以包含一組條件。

### 9.2 多空模式

支援兩種模式：

```text
模式 1：多空鏡像
模式 2：多空不對稱
```

#### 9.2.1 多空鏡像

空單邏輯由多單邏輯反向產生。

#### 9.2.2 多空不對稱

多單與空單可以使用不同進出場條件。

此功能對指數期貨重要，因為上漲與下跌的市場結構往往不同。

### 9.3 Rule Block Library

MVP 進場條件類型：

1. 價格突破：
   - Close > HighestHigh(N)
   - Close < LowestLow(N)
2. 均線交叉：
   - SMA(fast) crosses above SMA(slow)
   - SMA(fast) crosses below SMA(slow)
3. 均線濾網：
   - Close > SMA(N)
   - Close < SMA(N)
4. 震盪指標：
   - RSI < threshold
   - RSI > threshold
   - KD 類條件
   - MACD 類條件
5. 波動條件：
   - ATR > ATR_MA
   - ATR < ATR_MA
6. 時間條件：
   - 只在指定時間範圍交易
   - 避開指定時間範圍

Alpha 延後：

1. 成交量條件。
2. 多時間框架條件。
3. ATR 停損。
4. 移動停損。

### 9.4 出場方式

MVP 支援：

1. 反向訊號出場。
2. 固定停損。
3. 固定停利。
4. 持有 N 根 K 棒後出場。
5. Session 結束前出場。

Alpha 支援：

1. ATR 停損。
2. 移動停損。
3. 分批出場。
4. 初階加碼。

### 9.5 Condition Composer

MVP 支援：

1. 單一條件。
2. 多條件 AND。
3. 多條件 OR。
4. 簡單 AND / OR 混合。

Beta 支援：

1. 巢狀條件。
2. 樹狀結構。
3. Genetic Programming 條件樹。

### 9.6 Parameter Space Manager

支援：

1. 固定範圍隨機。
2. 使用者設定參數範圍。
3. 內建預設參數池。
4. 整數參數。
5. 浮點數參數。
6. 週期參數。
7. 閾值參數。

範例：

```json
{
  "SMA_PERIOD": {
    "type": "int",
    "min": 5,
    "max": 100,
    "step": 1
  },
  "RSI_THRESHOLD": {
    "type": "float",
    "min": 20,
    "max": 80,
    "step": 1
  }
}
```

### 9.7 Random Strategy Generator

MVP 生成方式：

1. 固定模板 + 隨機參數。
2. 固定模板 + 隨機條件組合。
3. 隨機組合進出場條件。
4. 隨機 stop loss / take profit / holding bars。
5. 隨機多空鏡像或不對稱設定。

### 9.8 Genetic Algorithm

Alpha 階段加入。

初版 GA 可包含：

1. 初始族群。
2. Fitness 評分。
3. Selection。
4. Crossover。
5. Mutation。
6. Elitism。
7. 停止條件。

### 9.9 Genetic Programming

Beta 階段加入。

GP 目標：

1. 支援樹狀策略條件。
2. 支援非線性巢狀條件。
3. 支援更自由的條件組合。
4. 支援更接近 AdapTrade Builder 的策略生成體驗。

---

## 10. Fitness Function 與淘汰規則

### 10.1 Fitness Function 原則

不能只最大化淨利。

單純最大化淨利容易產生 curve fitting 策略。

MVP 使用多指標加權評分：

```text
Fitness Score =
  Net Profit Score
+ Profit Factor Score
+ Max Drawdown Penalty
+ Avg Trade Score
+ OOS Performance Score
+ Trade Count Stability Score
+ IS/OOS Stability Score
+ Stress Test Survival Score
+ Monte Carlo Robustness Score
+ Walk-forward Pass Score
```

### 10.2 評分指標

1. Net Profit。
2. Profit Factor。
3. Max Drawdown。
4. Avg Trade。
5. Sharpe。
6. Sortino。
7. Win Rate。
8. Trade Count。
9. OOS Net Profit。
10. OOS Profit Factor。
11. OOS / IS Stability。
12. Stress Test Survival Score。
13. Monte Carlo Robustness Score。
14. Walk-forward Pass Rate。

### 10.3 內建淘汰規則

MVP 內建常用規則：

1. 最少交易次數。
2. 最小 Profit Factor。
3. 最大 Max Drawdown。
4. 最小 Avg Trade。
5. OOS 必須為正。
6. IS/OOS 不可差距過大。
7. 壓力測試至少通過指定項數。
8. Monte Carlo 結果不可過差。
9. Walk-forward 結果不可過差。

範例：

```text
Trade Count < 50 → 淘汰
Profit Factor < 1.2 → 淘汰
OOS Net Profit <= 0 → 淘汰
Max Drawdown > 使用者設定上限 → 淘汰
Avg Trade < 成本 2 倍 → 淘汰
Stress Test Pass Count < 3 → 淘汰
```

### 10.4 Alpha 自訂規則

Alpha 階段加入自訂淘汰規則 UI。

---

## 11. Backtest Engine

### 11.1 回測架構

MVP 採事件驅動 event-driven 架構，逐根 K 棒模擬。

```text
載入 Backtest Dataset
  ↓
套用 Session Filter
  ↓
逐根 K 棒處理
  ↓
計算策略條件
  ↓
判斷進出場
  ↓
檢查停損 / 停利 / 持有時間 / Session 結束
  ↓
套用手續費與滑價
  ↓
更新部位
  ↓
記錄交易
  ↓
更新權益曲線
  ↓
計算績效指標
```

### 11.2 部位規則

MVP：

1. 同時間只能持有一個部位。
2. 支援多單。
3. 支援空單。
4. 不支援多空同時持倉。
5. 不支援加碼。
6. 不支援分批出場。
7. 不支援 pyramiding。

Alpha：

1. 分批出場。
2. 初階加碼。

Beta：

1. 更完整 position sizing。
2. 多商品投組級回測。

### 11.3 成交假設

使用者可選：

1. 當根 Close 成交。
2. 下一根 Open 成交。
3. 當根 Open 成交。
4. 自訂成交模式。

建議預設：

```text
訊號於當根收盤確認，下一根 Open 成交
```

### 11.4 訂單類型

MVP 支援：

1. Market Order。
2. Stop Loss。
3. Take Profit。

延後支援：

1. Trailing Stop。
2. Limit Order。
3. Stop Order。

### 11.5 停損停利同根觸發規則

同一根 K 棒若 high 觸及停利且 low 觸及停損，真實盤中順序未知。

MVP 預設採保守法：

```text
同根 K 棒同時觸發停損與停利 → 先算停損
```

UI 提供選項：

1. Conservative：先算停損。
2. Optimistic：先算停利。
3. Bar Direction Guess：依 K 棒方向推測。
4. Skip Ambiguous Bar：跳過或標記不明確 K 棒。

### 11.6 交易成本

MVP 支援：

1. 固定每筆手續費。
2. 每口手續費。
3. 百分比成本。
4. 固定滑價 ticks。
5. 滑價點數。
6. 加倍壓力測試。

### 11.7 報酬計算

MVP 支援：

1. 點數損益。
2. 金額損益。
3. 百分比報酬。
4. 固定口數。

Alpha / Beta 延後：

1. 固定資金比例。
2. 波動率調整。
3. 風險百分比 position sizing。
4. 投組級資金配置。

---

## 12. Validation Engine

### 12.1 資料切分

支援：

1. 比例輸入。
2. 日期輸入。
3. 視覺化拖拉切分。
4. 顯示每段根數。
5. 顯示每段日期範圍。

切分模式：

```text
Training
Validation
Out-of-Sample
```

### 12.2 OOS 通過標準

內建規則：

1. OOS Net Profit > 0。
2. OOS Profit Factor > 使用者設定門檻。
3. OOS Max Drawdown 不超過 IS 的指定倍數。
4. OOS Trade Count 不可過少。
5. OOS Equity Curve 不可嚴重惡化。
6. IS/OOS 落差不可過大。

### 12.3 Stress Test

MVP 壓力測試：

1. 手續費加倍。
2. 滑價加倍。
3. 參數擾動 ±10%。
4. 隨機漏單。
5. 交易延遲一根 K。

延後：

1. 移除最佳 N 筆交易。
2. 價格資料加入噪音。
3. 更複雜流動性假設。

### 12.4 Monte Carlo

MVP：

1. 隨機漏單。
2. 隨機滑價擾動。

Alpha：

1. 隨機打亂交易順序。
2. Bootstrap 抽樣。
3. 多次模擬信賴區間。
4. 95% worst-case equity curve。

### 12.5 Walk-forward

使用者希望最終支援 Walk-forward Matrix。

分期：

#### MVP v0.1

1. 簡單固定視窗 Walk-forward。
2. 固定訓練區間 + 固定測試區間。
3. 產生基本 Walk-forward 結果摘要。

#### Alpha v0.2

1. 多組訓練 / 測試視窗比較。
2. Walk-forward 結果表。
3. Walk-forward 圖表。

#### Beta v0.3

1. Walk-forward Matrix。
2. 參數重新最佳化流程。
3. Walk-forward 結果納入 Fitness Score。

---

## 13. UI / UX 設計

### 13.1 技術選型

使用：

```text
PySide6
```

理由：

1. 適合桌面 GUI。
2. 授權與未來性較好。
3. 與使用者現有 PyQt 經驗相近。
4. 適合建立資料表格、設定頁、圖表嵌入、專案式工作區。

### 13.2 主視窗架構

```text
Main Window
├─ Top Toolbar
│  ├─ New Project
│  ├─ Open Project
│  ├─ Save
│  ├─ Run
│  ├─ Pause
│  ├─ Stop
│  └─ Export Report
│
├─ Left Navigation
│  ├─ Dashboard
│  ├─ Data
│  ├─ Build
│  ├─ Backtest
│  ├─ Validate
│  ├─ Results
│  ├─ Report
│  └─ Settings
│
├─ Main Workspace
│  └─ 顯示目前頁面的表格、設定、圖表、報告
│
├─ Right Inspector
│  └─ 顯示目前選取資料集 / 策略 / 報告摘要
│
└─ Bottom Log Panel
   └─ 顯示生成進度、錯誤、任務狀態
```

### 13.3 Dashboard

功能：

1. 最近專案。
2. 最近資料集。
3. 最近生成任務。
4. 最近通過策略。
5. 最近報告。

MVP 做簡版。

### 13.4 Data Page

功能：

1. 匯入資料。
2. 顯示 OHLCV 表格。
3. 顯示 K 線預覽。
4. 顯示資料品質檢查。
5. 設定商品 profile。
6. 設定 session。
7. 執行 resample。
8. 顯示 resample 後資料摘要。

### 13.5 Build Setup Page

使用分段式設定：

```text
Build Setup
├─ Rules
├─ Parameters
├─ Fitness
├─ Filters
├─ Stop Conditions
├─ Data Split
└─ Run Configuration
```

### 13.6 策略條件設定 UI

MVP：

1. GUI 勾選條件積木。
2. 下拉選指標。
3. 下拉選運算子。
4. 設定參數範圍。
5. 設定條件組合 AND / OR。

Alpha：

1. 類公式條件編輯器。
2. 進階模式手輸公式。

### 13.7 資料切分 UI

支援：

1. 比例輸入。
2. 日期輸入。
3. 時間軸拖拉 Training / Validation / OOS。
4. 顯示每段資料根數。
5. 顯示每段日期範圍。

### 13.8 策略生成進行中畫面

顯示：

1. 已生成策略數。
2. 通過篩選數。
3. 當前最佳 Fitness。
4. 即時排行榜。
5. 即時權益曲線預覽。
6. CPU / 任務進度。
7. 可暫停。
8. 可停止。

### 13.9 Results Page

策略排行榜欄位：

1. Strategy ID。
2. Fitness Score。
3. Net Profit。
4. Profit Factor。
5. Max Drawdown。
6. Avg Trade。
7. Win Rate。
8. Trade Count。
9. OOS Net Profit。
10. OOS PF。
11. Stress Pass Count。
12. Walk-forward Pass。

功能：

1. 欄位排序。
2. 篩選。
3. 通過 / 失敗標籤。
4. 風險顏色標記。
5. 策略比較視窗。

### 13.10 Strategy Detail Page

頁籤：

1. Summary。
2. Equity Curve。
3. Drawdown。
4. Trades。
5. Entry / Exit Rules。
6. IS / OOS Compare。
7. Stress Test。
8. Monte Carlo。
9. Walk-forward。
10. Export。

### 13.11 Report Page

MVP 匯出：

1. Excel。
2. HTML。
3. Markdown。
4. Strategy JSON。
5. Pseudo Code。

延後：

1. PDF。
2. Python 策略碼。
3. NinjaTrader / EasyLanguage。

### 13.12 視覺化工具

MVP 使用：

1. Matplotlib。
2. PyQtGraph。
3. Plotly HTML 報告。

建議用途：

```text
PyQtGraph：即時或互動式 GUI 圖表
Matplotlib：穩定靜態圖
Plotly：HTML 報告互動圖
```

---

## 14. 專案資料保存設計

### 14.1 每個研究專案資料夾

```text
quant_strategy_lab_project/
├─ project.sqlite
├─ project.json
├─ data/
│  ├─ raw/
│  ├─ normalized/
│  └─ resampled/
├─ strategies/
│  ├─ generated/
│  ├─ passed/
│  └─ archived/
├─ reports/
│  ├─ html/
│  ├─ markdown/
│  └─ excel/
├─ logs/
├─ exports/
│  ├─ json/
│  └─ pseudocode/
└─ config/
   ├─ instruments.json
   ├─ sessions.json
   └─ app_settings.json
```

### 14.2 原始資料保存策略

支援選項：

1. 複製原始資料進專案資料夾。
2. 只記錄原始路徑。
3. 大型資料建立索引，不複製。

MVP 使用可選模式。

---

## 15. SQLite 資料庫設計初稿

### 15.1 projects

用途：保存專案資訊。

欄位：

```text
id
name
created_at
updated_at
root_path
description
version
```

### 15.2 datasets

用途：保存資料集資訊。

欄位：

```text
id
project_id
name
symbol
timeframe
source_type
source_path
normalized_path
row_count
start_datetime
end_datetime
created_at
```

### 15.3 instruments

用途：保存商品設定。

欄位：

```text
id
symbol
name
market
tick_size
point_value
commission_type
commission_value
slippage_type
slippage_value
currency
session_template_id
```

### 15.4 sessions

用途：保存交易時段模板。

欄位：

```text
id
name
timezone
session_json
description
```

### 15.5 build_tasks

用途：保存每次策略生成任務。

欄位：

```text
id
project_id
dataset_id
name
config_json
random_seed
status
started_at
finished_at
generated_count
passed_count
best_fitness
```

### 15.6 strategies

用途：保存策略。

欄位：

```text
id
project_id
build_task_id
strategy_uid
name
strategy_json
pseudo_code
status
fitness_score
created_at
```

### 15.7 strategy_rules

用途：保存策略規則摘要。

欄位：

```text
id
strategy_id
block_name
rule_json
description
```

### 15.8 backtest_results

用途：保存回測結果。

欄位：

```text
id
strategy_id
dataset_id
segment
net_profit
profit_factor
max_drawdown
avg_trade
win_rate
trade_count
sharpe
sortino
created_at
```

### 15.9 trades

用途：保存交易明細。

欄位：

```text
id
backtest_result_id
strategy_id
entry_datetime
exit_datetime
direction
entry_price
exit_price
quantity
gross_pnl
commission
slippage
net_pnl
bars_held
exit_reason
```

### 15.10 equity_curves

用途：保存權益曲線。

欄位：

```text
id
backtest_result_id
datetime
equity
drawdown
position
```

### 15.11 validation_results

用途：保存 OOS / Validation 結果。

欄位：

```text
id
strategy_id
validation_type
config_json
result_json
passed
score
created_at
```

### 15.12 stress_test_results

用途：保存壓力測試結果。

欄位：

```text
id
strategy_id
test_type
config_json
net_profit
profit_factor
max_drawdown
passed
created_at
```

### 15.13 monte_carlo_results

用途：保存 Monte Carlo 結果。

欄位：

```text
id
strategy_id
config_json
runs
summary_json
worst_case_drawdown
confidence_level
passed
created_at
```

### 15.14 walk_forward_results

用途：保存 Walk-forward 結果。

欄位：

```text
id
strategy_id
config_json
window_count
pass_count
pass_rate
summary_json
created_at
```

### 15.15 reports

用途：保存報告資訊。

欄位：

```text
id
project_id
strategy_id
report_type
file_path
created_at
```

### 15.16 logs

用途：保存任務與錯誤紀錄。

欄位：

```text
id
project_id
task_id
level
message
created_at
```

---

## 16. 軟體工程目錄設計

```text
quant_strategy_lab/
├─ app/
│  ├─ main.py
│  ├─ ui/
│  │  ├─ main_window.py
│  │  ├─ dashboard_page.py
│  │  ├─ data_page.py
│  │  ├─ build_page.py
│  │  ├─ backtest_page.py
│  │  ├─ validate_page.py
│  │  ├─ results_page.py
│  │  ├─ report_page.py
│  │  └─ settings_page.py
│  ├─ widgets/
│  │  ├─ chart_widget.py
│  │  ├─ dataframe_view.py
│  │  ├─ strategy_table.py
│  │  └─ log_panel.py
│  └─ resources/
│
├─ core/
│  ├─ models/
│  │  ├─ dataset.py
│  │  ├─ instrument.py
│  │  ├─ strategy.py
│  │  ├─ trade.py
│  │  └─ result.py
│  ├─ schemas/
│  └─ utils/
│
├─ data_engine/
│  ├─ importers/
│  │  ├─ csv_importer.py
│  │  ├─ excel_importer.py
│  │  └─ multicharts_importer.py
│  ├─ normalizer.py
│  ├─ resampler.py
│  ├─ session_filter.py
│  ├─ instrument_profile.py
│  └─ quality_checker.py
│
├─ strategy_engine/
│  ├─ rule_blocks/
│  │  ├─ price_rules.py
│  │  ├─ ma_rules.py
│  │  ├─ oscillator_rules.py
│  │  ├─ volatility_rules.py
│  │  └─ time_rules.py
│  ├─ parameter_space.py
│  ├─ template_engine.py
│  ├─ condition_composer.py
│  ├─ random_generator.py
│  ├─ fitness.py
│  └─ elimination.py
│
├─ backtest_engine/
│  ├─ event_engine.py
│  ├─ order_model.py
│  ├─ position.py
│  ├─ execution_model.py
│  ├─ trade_recorder.py
│  └─ metrics.py
│
├─ validation_engine/
│  ├─ data_split.py
│  ├─ oos_validator.py
│  ├─ stress_test.py
│  ├─ monte_carlo.py
│  └─ walk_forward.py
│
├─ repository/
│  ├─ sqlite_repo.py
│  ├─ project_repo.py
│  ├─ dataset_repo.py
│  ├─ strategy_repo.py
│  ├─ result_repo.py
│  └─ report_repo.py
│
├─ reports/
│  ├─ excel_report.py
│  ├─ html_report.py
│  ├─ markdown_report.py
│  └─ pseudocode_exporter.py
│
├─ tests/
│  ├─ test_data_import.py
│  ├─ test_resampler.py
│  ├─ test_session_filter.py
│  ├─ test_strategy_generator.py
│  ├─ test_backtest_engine.py
│  ├─ test_stress_test.py
│  └─ test_reports.py
│
├─ docs/
│  ├─ PRD.md
│  ├─ architecture.md
│  ├─ task_board.md
│  └─ changelog.md
│
├─ sample_data/
├─ pyproject.toml
└─ README.md
```

---

## 17. 三模型協作流程

### 17.1 整體原則

本專案採單一目錄、多人模型協作模式。

所有模型共用同一個專案目錄與文件。

禁止：

1. 各自建立不同架構。
2. 不讀文件直接修改。
3. 在 GUI 裡硬塞核心邏輯。
4. 未更新 changelog。
5. 未寫測試即宣稱完成核心模組。

### 17.2 Codex 角色

Codex 因 quota 較有限，負責高階工程、複核、改善、架構審查與任務分派。

Codex 任務：

1. 閱讀 PRD.md。
2. 閱讀 architecture.md。
3. 閱讀 task_board.md。
4. 拆分下一個子任務。
5. 指派給 Anti-Gravity 或 DeepSeek。
6. 收到結果後整合。
7. 複核程式碼品質。
8. 修正架構偏差。
9. 每完成一個子任務後停下來。
10. 輸出下一步模型分派指令。

### 17.3 Anti-Gravity 角色

Anti-Gravity 負責打頭陣與初階工程。

適合任務：

1. 建立專案骨架。
2. 建立 PySide6 基礎視窗。
3. 建立 Dashboard 草稿。
4. 建立 Data Page 初稿。
5. 建立設定表單。
6. 建立報告樣板。
7. 建立文件初稿。
8. 實作非核心高風險功能。

不建議 Anti-Gravity 單獨負責：

1. 回測核心。
2. 策略生成演算法。
3. Monte Carlo。
4. Walk-forward。
5. 效能優化。

### 17.4 DeepSeek V4 Pro 角色

DeepSeek V4 Pro 負責主力工程與進階工程。

適合任務：

1. Data Engine。
2. Strategy Engine。
3. Backtest Engine。
4. Validation Engine。
5. Fitness Function。
6. Elimination Filter。
7. Monte Carlo。
8. Walk-forward。
9. 效能優化。
10. 過度擬合風險審查。

### 17.5 任務交接格式

每個模型完成任務後，必須回報：

```text
1. 完成內容
2. 修改檔案
3. 新增檔案
4. 測試方式
5. 測試結果
6. 已知問題
7. 下一步建議
```

### 17.6 Codex 每階段停下規則

Codex 不應無限連續開發。

每完成一個子任務後，必須停下並輸出：

```text
目前狀態：
已完成：
未完成：
風險：
下一步應分派給：
下一步 Prompt：
驗收標準：
```

---

## 18. 開發里程碑

### 18.1 Prototype v0.0.1

目標：建立第一個可執行版本。

驗收標準：

1. 啟動 PySide6 主視窗。
2. 建立或開啟專案資料夾。
3. 匯入一份 MultiCharts / TradeStation 類 OHLCV 資料。
4. 顯示資料表格。
5. 顯示 K 線圖。
6. 將 1 分 K resample 成 5 分 K。
7. 設定商品 profile。
8. 手動建立一條簡單策略。
9. 跑事件驅動回測。
10. 顯示交易明細。
11. 顯示權益曲線。
12. 生成 10 條隨機策略。
13. 顯示策略排行榜。
14. 匯出簡單 Markdown 或 HTML 報告。

### 18.2 MVP v0.1

目標：完成單商品策略生成與驗證流水線。

功能：

1. 完整 Data Engine 初版。
2. 固定模板策略生成。
3. 單商品事件驅動回測。
4. IS / Validation / OOS。
5. 壓力測試。
6. 基礎 Monte Carlo。
7. 基礎 Walk-forward。
8. 策略排行榜。
9. 策略詳細報告。
10. Excel / HTML / Markdown / JSON / Pseudo Code 匯出。

### 18.3 Alpha v0.2

目標：加入演化與更強驗證。

功能：

1. 簡單 Genetic Algorithm。
2. 多商品交叉驗證。
3. 多時間框架條件。
4. 成交量條件。
5. 自訂淘汰規則。
6. Monte Carlo 強化。
7. Walk-forward 強化。
8. 公式條件編輯器。

### 18.4 Beta v0.3

目標：接近專業研究平台。

功能：

1. Genetic Programming 樹狀結構。
2. Walk-forward Matrix。
3. 多商品投組回測。
4. 完整 position sizing。
5. Python 策略碼匯出。
6. PDF 報告。
7. 類 IDE 專案工作區。

### 18.5 v1.0 正式版

目標：形成穩定可長期使用的桌面策略研究平台。

功能：

1. 穩定專案管理。
2. 完整策略生成與驗證。
3. 強化視覺化。
4. 完整報告。
5. 可擴充引擎。
6. 可重現實驗紀錄。
7. 穩定測試覆蓋。

---

## 19. 測試計畫

### 19.1 Data Engine 測試

1. CSV 匯入測試。
2. MultiCharts 類格式匯入測試。
3. datetime 解析測試。
4. 欄位標準化測試。
5. 缺值檢查測試。
6. 重複 datetime 測試。
7. OHLC 合法性測試。
8. resample 測試。
9. session filter 測試。
10. instrument profile 測試。

### 19.2 Strategy Engine 測試

1. Rule block 計算測試。
2. SMA 測試。
3. RSI 測試。
4. ATR 測試。
5. 價格突破條件測試。
6. AND / OR 條件組合測試。
7. 隨機策略生成測試。
8. 策略 JSON 序列化測試。
9. Pseudo Code 匯出測試。

### 19.3 Backtest Engine 測試

1. Market order 成交測試。
2. Next Open 成交測試。
3. Close 成交測試。
4. Stop Loss 測試。
5. Take Profit 測試。
6. 同根停損停利觸發測試。
7. session 結束出場測試。
8. 手續費計算測試。
9. 滑價計算測試。
10. 多空交易測試。
11. 權益曲線測試。
12. Max Drawdown 測試。

### 19.4 Validation Engine 測試

1. IS / Validation / OOS 切分測試。
2. OOS 通過規則測試。
3. 手續費加倍測試。
4. 滑價加倍測試。
5. 參數擾動測試。
6. 隨機漏單測試。
7. 交易延遲測試。
8. Monte Carlo 測試。
9. Walk-forward 測試。

### 19.5 UI 測試

1. 主視窗啟動測試。
2. 專案建立測試。
3. 資料匯入 UI 測試。
4. K 線圖顯示測試。
5. Build Setup 表單測試。
6. 策略排行榜測試。
7. 策略詳細頁測試。
8. 報告匯出測試。

### 19.6 報告測試

1. Markdown 報告產生測試。
2. HTML 報告產生測試。
3. Excel 報告產生測試。
4. JSON 策略匯出測試。
5. Pseudo Code 匯出測試。

---

## 20. 開發管理規則

### 20.1 文件優先

每次開發前必讀：

1. docs/PRD.md。
2. docs/architecture.md。
3. docs/task_board.md。

### 20.2 修改後必更新

每次修改後必更新：

1. docs/changelog.md。
2. 若有架構變更，更新 docs/architecture.md。
3. 若有任務狀態變更，更新 docs/task_board.md。

### 20.3 分層禁止事項

禁止：

1. 在 UI 中直接寫回測核心。
2. 在 UI 中直接寫策略生成邏輯。
3. 在回測引擎中直接操作 GUI。
4. 在核心引擎中硬寫檔案路徑。
5. 不經 Repository layer 亂寫資料庫。
6. 不留測試就修改核心邏輯。

### 20.4 每個子任務驗收標準

每個任務需包含：

1. 任務目標。
2. 修改檔案。
3. 輸入。
4. 輸出。
5. 測試方式。
6. 驗收標準。
7. 失敗處理。

---

## 21. 主要風險

### 21.1 功能範圍過大

使用者希望功能完整，但第一版必須嚴格切分。

風險：

```text
MVP 變成大型商業軟體複製計畫
```

對策：

1. 嚴格遵守 MVP 範圍。
2. GA、GP、完整 Walk-forward Matrix 延後。
3. 先完成端到端流程。

### 21.2 GUI 與 Engine 黏死

風險：

```text
後期難測試、難維護、難擴充
```

對策：

1. engine 獨立 package。
2. UI 只呼叫 service / engine API。
3. 核心模組需有測試。

### 21.3 過早開發 Genetic Programming

風險：

```text
策略結構過度複雜，第一版失控
```

對策：

1. MVP 固定四區塊。
2. Alpha GA。
3. Beta GP。

### 21.4 過早開發完整 Walk-forward Matrix

風險：

```text
參數最佳化、視窗組合與報告複雜度暴增
```

對策：

1. MVP 簡單 Walk-forward。
2. Alpha 多視窗。
3. Beta Matrix。

### 21.5 回測速度不足

風險：

```text
策略生成大量回測時速度過慢
```

對策：

1. 初版正確性優先。
2. 熱點模組再用 numpy / numba。
3. 先單商品，後多商品。
4. 先隨機生成，後 GA / GP。

### 21.6 過度擬合

風險：

```text
生成大量漂亮但無法實盤存活的策略
```

對策：

1. OOS。
2. 壓力測試。
3. Monte Carlo。
4. Walk-forward。
5. Avg Trade 門檻。
6. IS/OOS 穩定性。
7. 通過門檻與淘汰規則。

### 21.7 三模型架構混亂

風險：

```text
Anti-Gravity、DeepSeek、Codex 各寫各的
```

對策：

1. 單一專案目錄。
2. 每次修改前讀 architecture.md。
3. 每次修改後更新 changelog.md。
4. Codex 負責整合與任務分派。
5. DeepSeek 負責核心工程。
6. Anti-Gravity 負責骨架與 UI 初稿。

---

## 22. Roadmap

```text
v0.0.1 Prototype
  資料匯入 + K 線 + 單策略回測 + 10 條策略排行

v0.1 MVP
  完整單商品策略生成與驗證流水線

v0.2 Alpha
  GA、多商品交叉驗證、Monte Carlo / Walk-forward 強化

v0.3 Beta
  GP、Walk-forward Matrix、多商品投組、Python 策略匯出

v1.0 正式版
  完整桌面策略研究平台
```

---

## 23. Prototype v0.0.1 具體任務拆解

### 23.1 Task 001：建立專案骨架

負責模型：Anti-Gravity  
複核模型：Codex  

內容：

1. 建立工程目錄。
2. 建立 pyproject.toml。
3. 建立 README.md。
4. 建立 docs/PRD.md。
5. 建立 docs/architecture.md。
6. 建立 docs/task_board.md。
7. 建立 docs/changelog.md。
8. 建立 app/main.py。
9. 建立基本 PySide6 主視窗。

驗收：

1. 可執行 `python app/main.py`。
2. 可看到主視窗。
3. 左側導航存在。
4. docs 文件存在。

### 23.2 Task 002：建立 Project Manager

負責模型：DeepSeek  
複核模型：Codex  

內容：

1. 建立 project folder。
2. 建立 project.sqlite。
3. 建立 project.json。
4. 建立基本目錄：
   - data/
   - strategies/
   - reports/
   - logs/
   - config/

驗收：

1. 可建立新專案。
2. 可開啟既有專案。
3. SQLite 可初始化基本 tables。

### 23.3 Task 003：Data Importer 初版

負責模型：DeepSeek  
複核模型：Codex  

內容：

1. 匯入 CSV / MultiCharts 類 OHLCV。
2. 標準化欄位。
3. 顯示資料表格。
4. 儲存 normalized data。

驗收：

1. 可匯入 sample data。
2. 可顯示前 100 筆。
3. 可檢查欄位完整性。

### 23.4 Task 004：K 線與 Resample

負責模型：Anti-Gravity + DeepSeek  
複核模型：Codex  

內容：

1. 顯示 K 線圖。
2. 1 分 K 轉 5 分 K。
3. 顯示轉換前後資料摘要。

驗收：

1. K 線圖可見。
2. Resample 後 OHLCV 正確。
3. 表格可切換原始 / 轉換後資料。

### 23.5 Task 005：簡單策略與回測

負責模型：DeepSeek  
複核模型：Codex  

內容：

1. 建立簡單策略格式。
2. 建立事件驅動回測。
3. 支援 SMA crossover 或 Close > SMA。
4. 產生 trades。
5. 產生 equity curve。

驗收：

1. 手動建立一條策略。
2. 可回測。
3. 顯示交易明細。
4. 顯示 equity curve。

### 23.6 Task 006：隨機策略生成與排行榜

負責模型：DeepSeek  
複核模型：Codex  

內容：

1. 生成 10 條隨機策略。
2. 每條策略跑回測。
3. 計算基本績效。
4. 顯示排行榜。

驗收：

1. 可生成 10 條策略。
2. 可看到 Fitness / Net Profit / PF / Max DD。
3. 可點選策略查看詳情。

### 23.7 Task 007：簡單報告匯出

負責模型：Anti-Gravity  
複核模型：Codex  

內容：

1. 匯出 Markdown。
2. 匯出 HTML。
3. 包含策略摘要、績效、權益曲線圖路徑或嵌入圖。

驗收：

1. 可產生報告檔。
2. 報告可開啟。
3. 報告內容與策略結果一致。

---

## 24. 給 Codex 的第一階段開工原則

Codex 開工時必須遵守：

1. 不要一次實作全部。
2. 先建立專案骨架。
3. 先建立 docs。
4. 先確認架構。
5. 完成 Task 001 後停下。
6. 產生下一步給 Anti-Gravity 或 DeepSeek 的明確指令。
7. 不准擅自跳到 GA / GP / Walk-forward Matrix。
8. 不准先做實盤下單。
9. 不准讓 UI 和 engine 黏死。
10. 不准省略 changelog。

---

## 25. 附錄：核心設計決策摘要

### 25.1 使用者已確認決策

1. 產品主軸：生成 + 回測 + OOS 篩選。
2. 目標市場：通用 OHLCV，不綁單一市場。
3. 資料週期：支援 1 分 K 以上，Tick 延後。
4. 實盤下單：第一版不做。
5. UI：PySide6 桌面。
6. 視覺化：MVP 就要完整。
7. 策略生成：MVP 隨機 / 固定模板，Alpha GA，Beta GP。
8. 策略結構：MVP 固定四區塊。
9. 回測：事件驅動。
10. 防擬合：OOS、壓力測試、Monte Carlo、Walk-forward。
11. 報告：Excel / HTML / Markdown / JSON / Pseudo Code。
12. 專案保存：資料夾 + SQLite。
13. 模型分工：Anti-Gravity 初階、DeepSeek 主力、Codex 高階複核。

### 25.2 MVP 成功定義

MVP 成功不是「做出最強策略」，而是：

```text
能完整走完一次策略研究流程，
並能用視覺化與防擬合測試，
篩出較可靠的候選策略。
```

---

## 26. 結語

Quant Strategy Lab 的第一階段重點不是追求華麗演算法，而是建立一個穩定、可視化、可重現、可驗證的策略研究基礎平台。

只要 Prototype v0.0.1 能成功完成：

```text
資料匯入
→ K 線顯示
→ Resample
→ 單策略回測
→ 隨機生成 10 條策略
→ 排行
→ 報告匯出
```

這個專案就已經從概念進入可落地階段。

後續再逐步加入 GA、GP、Walk-forward Matrix、多商品驗證與策略碼匯出，避免第一版就陷入過大範圍。

---
