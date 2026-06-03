# Stock Analysis Platform - MVP Specification

## Project Overview
- **Name**: 台股資料分析平台 (Stock Analysis Platform)
- **Type**: Web Application (Flask + Tailwind CSS)
- **Core**: 提供台股投資人快速查看大盤、個股資訊的輔助平台
- **Target Users**: 台股投資人、研究人員

## Technology Stack
- Backend: Flask (Python)
- Frontend: Tailwind CSS + Lightweight Charts (TradingView)
- Database: SQLite (MVP), 可擴展至 PostgreSQL/SQL Server
- Data Source: FinMind API

## MVP Features (Priority 0)

### 1. 首頁顯示台股大盤 K 線圖
- 使用 Lightweight Charts 繪製
- 切換 1分/5分/15分/日K
- 顯示開高低收、成交量

### 2. 首頁顯示台積電 (2330) K 線圖
- 獨立圖表區塊
- 顯示即時價格、漲跌幅

### 3. 大盤即時摘要卡片
- 加權指數（含漲跌）
- 成交金額
- 上漲/下跌家數
- 外資買賣超

### 4. 個股查詢頁面
- 輸入股票代號查詢
- 顯示基本資料、K線圖、法人買賣超

## UI/UX Specification

### Layout
- Header: 導航列（大盤、個股、法人、回測）
- Main: 響應式網格佈局
- Footer: 版權說明

### Color Scheme
- Primary: #1e3a8a (深藍)
- Accent Green: #10b981
- Accent Red: #ef4444
- Background: #f8fafc
- Card BG: #ffffff

### Typography
- 字體: Inter, system-ui
- 標題: 24px/20px/16px
- 內文: 14px

## Acceptance Criteria
1. 首頁能正確顯示大盤 K 線圖
2. 台積電 K 線圖能正確渲染
3. 摘要卡片顯示真實數據（若API無法取得則顯示錯誤訊息）
4. 個股查詢頁面能輸入代號查詢
5. 網站能在本地正常運行 (localhost:5000)

---

## 編輯記錄 (Edit History)

### 2026-06-03 - MVP 初始版本
- 建立 Flask 專案結構
- 實作首頁大盤 K 線圖 + 台積電 K 線圖
- 實作摘要卡片
- 實作個股查詢頁面
- 使用 FinMind API 取得資料，fallback 到 mock data

### 2026-06-03 - 移除模擬資料
- 修正：不使用模擬資料，API 失敗時顯示錯誤訊息
- 修正 getTaiwanWeightedIndex()：API 失敗時返回 error dict 而非 fallback
- 修正 get_kline_data()：API 失敗時返回 error list 而非 fallback
- 修正 FinMind API dataset：TaiwanWeightedIndexPrice → TaiwanVariousIndicatorsPrice
- 模板加入 error 訊息顯示

### 待完成
- [x] get_institutional_trades() 移除 fallback mock data → 现返回空数组
- [x] 改用 FinMind v4 API：`https://api.finmindtrade.com/api/v4/data`
- [x] 改用 Authorization: Bearer header 认证
- [x] 加權指數 dataset 改为 `TaiwanStockTotalReturnIndex` (data_id: TAIEX)
- [x] 個股 K線欄位映射：`max` → `high`, `min` → `low`, `Trading_Volume` → `volume`
- [x] get_stock_info() 改用 `TaiwanStockInfo` API（移除 mock data）
- [x] 模板改用新字段名（stock_name, stock_id, industry_category）