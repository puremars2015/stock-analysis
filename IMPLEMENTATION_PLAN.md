# Stock Analysis Platform - Complete Implementation Plan

## Project
台股資料分析平台 (Stock Analysis Platform) - 完整实施 (non-MVP)

## Tech Stack
- Backend: Flask + SQLAlchemy + pyodbc
- Database: SQL Server (port 1433, db: stock_analysis, sa/YourStrong!Passw0rd)
- Data Source: FinMind v4 API (token in .env)
- Frontend: Tailwind CSS + Lightweight Charts + ECharts

## 数据库 Schema (基于规划书第七章)

### 1. stock_master 股票主檔
- stock_id (PK, varchar)
- stock_name (varchar)
- market (varchar) -- 上市/上櫃
- industry (varchar)
- capital (bigint)
- listed_date (date)

### 2. stock_price_daily 日 K 資料
- id (PK, int identity)
- date (date)
- stock_id (varchar, FK)
- open (decimal)
- high (decimal)
- low (decimal)
- close (decimal)
- volume (bigint)
- amount (decimal)

### 3. institutional_trade 法人買賣超
- id (PK, int identity)
- date (date)
- stock_id (varchar)
- name (varchar) -- 外資/投信/自營商
- buy (decimal)
- sell (decimal)
- net (decimal) -- buy - sell

### 4. financial_statement 財報資料
- id (PK, int identity)
- year (int)
- quarter (int)
- stock_id (varchar)
- revenue (decimal)
- gross_profit (decimal)
- operating_income (decimal)
- net_income (decimal)
- eps (decimal)
- gross_margin (decimal)
- operating_margin (decimal)
- roe (decimal)

### 5. mops_announcement 公告資料
- id (PK, int identity)
- announce_time (datetime)
- stock_id (varchar)
- title (varchar)
- category (varchar)
- content (text)
- source_url (varchar)

### 6. user_watchlist 自選股
- id (PK, int identity)
- user_id (varchar)
- stock_id (varchar)
- group_name (varchar)
- created_at (datetime)

### 7. index_daily 大盤指數
- id (PK, int identity)
- date (date)
- index_id (varchar) -- TAIEX, TPEx
- open (decimal)
- high (decimal)
- low (decimal)
- close (decimal)
- volume (bigint)

### 8. margin_trade 融資融券
- id (PK, int identity)
- date (date)
- stock_id (varchar)
- margin_buy (decimal)
- margin_sell (decimal)
- short_buy (decimal)
- short_sell (decimal)
- margin_balance (decimal)
- short_balance (decimal)

## FinMind 数据集映射
- TaiwanStockInfo → stock_master
- TaiwanStockPrice → stock_price_daily
- TaiwanStockTotalReturnIndex → index_daily
- InstitutionalInvestorsBuySell → institutional_trade
- FinancialStatements → financial_statement
- TaiwanStockMonthRevenue → financial_statement (monthly)
- TaiwanStockMarginPurchaseShortSale → margin_trade
- TaiwanStockNews → mops_announcement

## 首頁 12 個區塊 (规划书十)
1. 今日台股大盤 K 線圖
2. 今日台積電 K 線圖
3. 大盤即時摘要卡片
4. 成交金額與市場量能
5. 上漲/下跌家數
6. 類股熱力圖 (用 stock_master.industry 分组计算涨跌幅)
7. 今日強勢股/弱勢股排行
8. 三大法人買賣超
9. 台指期與外資期貨未平倉
10. 選擇權 Put/Call Ratio
11. MOPS 重大訊息與月營收公告
12. AI 今日市場摘要與自選股清單

## 8 個功能頁面 (规划书四)
1. 大盤分析頁 /market
2. 個股分析頁 /stock
3. 法人籌碼頁 /institutional
4. 期貨與選擇權分析頁 /futures
5. 基本面分析頁 /fundamental
6. 選股器頁面 /screener
7. 回測分析頁 /backtest
8. 警示通知頁 /alerts

## 文件結構
```
stock-analysis/
├── app.py                  # Flask 主程式 (改用 SQLAlchemy)
├── config.py               # 配置 (DB connection, FinMind)
├── models.py               # SQLAlchemy models
├── database.py             # DB 初始化、session 管理
├── services/
│   ├── finmind.py          # FinMind API 客户端
│   ├── data_sync.py        # 数据同步 service
│   ├── indicators.py       # 技术指标计算 (MA, RSI, MACD, KD)
│   ├── screener.py         # 选股器逻辑
│   ├── backtest.py         # 回测引擎
│   ├── ai_summary.py       # AI 摘要生成
│   └── alerts.py           # 警示通知
├── routes/
│   ├── pages.py            # 页面路由
│   └── api.py              # API routes
├── scheduler.py            # APScheduler 定时任务
├── templates/
│   ├── base.html           # 基础模板
│   ├── index.html          # 首页 (12 区块)
│   ├── market.html         # 大盘分析
│   ├── stock.html          # 个股
│   ├── institutional.html  # 法人
│   ├── futures.html        # 期货选择权
│   ├── fundamental.html    # 基本面
│   ├── screener.html       # 选股器
│   ├── backtest.html       # 回测
│   └── alerts.html         # 警示
├── static/
│   ├── css/output.css
│   ├── js/
│   │   ├── charts.js       # Lightweight Charts 工具
│   │   ├── heatmap.js      # ECharts 热力图
│   │   └── main.js         # 主交互逻辑
├── SPEC.md                 # 规格
├── 網站規劃.md              # 详细规划
├── .env                    # 环境变量
└── requirements.txt        # 依赖
```

## 实施阶段
- 阶段 1: 数据层 (models, db, finmind client, data sync)
- 阶段 2: 数据抓取 + 初始化
- 阶段 3: API routes + 前端 templates
- 阶段 4: AI 摘要 + 选股 + 回测
