import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database import init_db, get_session
from models import StockInfo, StockPrice, InstitutionalTrade, TAIEXData, TaiwanStockTotalReturnIndex, StockIndicator, ScreenerCondition, BacktestResult

MONITORED_STOCKS = [
    ("2330", "台積電"),
    ("2317", "鴻海"),
    ("2454", "聯發科"),
    ("2303", "聯電"),
    ("3008", "大立光"),
    ("2412", "中華電"),
    ("2891", "中信金"),
    ("2881", "富邦金"),
    ("2892", "第一金"),
    ("2002", "中鋼"),
    ("2603", "長榮"),
    ("2609", "陽明"),
    ("2615", "萬海"),
    ("2886", "兆豐金"),
    ("5871", "中租-KY"),
    ("6505", "台塑"),
    ("1301", "台塑"),
    ("1326", "台化"),
    ("1718", "中纖"),
    ("2207", "和泰車"),
]

PRESETS = [
    {
        "name": "價值投資",
        "description": "本益比低、股價淨值比低的價值股",
        "conditions": '{"pe_ratio_max": 15, "pb_ratio_max": 1.5, "dividend_yield_min": 3.0}',
    },
    {
        "name": "成長股",
        "description": "營收成長、盈餘成長的成長股",
        "conditions": '{"revenue_growth_min": 20, "profit_growth_min": 15}',
    },
    {
        "name": "動能股",
        "description": "技術面強勢、RSI 未過熱",
        "conditions": '{"rsi_min": 50, "rsi_max": 75, "ma20_above_ma60": true}',
    },
    {
        "name": "高股息",
        "description": "現金股息殖利率 > 5%",
        "conditions": '{"dividend_yield_min": 5.0}',
    },
    {
        "name": "藍籌股",
        "description": "每日成交量 > 5000 張",
        "conditions": '{"volume_min": 5000000}',
    },
]


def main():
    print("[init_db] Creating tables...")
    init_db()

    session = get_session()
    try:
        print("[init_db] Adding monitored stocks...")
        for stock_id, stock_name in MONITORED_STOCKS:
            existing = session.query(StockInfo).filter_by(stock_id=stock_id).first()
            if not existing:
                session.add(StockInfo(stock_id=stock_id, stock_name=stock_name))
                print(f"  Added {stock_id} {stock_name}")
            else:
                print(f"  {stock_id} already exists")

        print("[init_db] Adding screener presets...")
        for preset in PRESETS:
            existing = session.query(ScreenerCondition).filter_by(name=preset["name"]).first()
            if not existing:
                session.add(ScreenerCondition(**preset))
                print(f"  Added preset: {preset['name']}")

        session.commit()
        print("[init_db] Done!")
    except Exception as e:
        session.rollback()
        print(f"[init_db] Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()