from database import get_session
from models import StockPrice, StockIndicator, StockInfo
from services.indicators import compute_indicators, kline_to_df
from services.finmind import client
import pandas as pd
from datetime import datetime, date, timedelta


SCREENER_PRESETS = {
    "value": {
        "name": "價值投資",
        "description": "本益比低、股價淨值比低的價值股",
        "conditions": {
            "pe_ratio_max": 15,
            "pb_ratio_max": 1.5,
            "dividend_yield_min": 3.0,
        },
    },
    "growth": {
        "name": "成長股",
        "description": "營收成長、盈餘成長的成長股",
        "conditions": {
            "revenue_growth_min": 20,
            "profit_growth_min": 15,
        },
    },
    "momentum": {
        "name": "動能股",
        "description": "技術面強勢、RSI 未過熱",
        "conditions": {
            "rsi_min": 50,
            "rsi_max": 75,
            "ma20_above_ma60": True,
        },
    },
    "high_div": {
        "name": "高股息",
        "description": "現金股息殖利率 > 5%",
        "conditions": {
            "dividend_yield_min": 5.0,
        },
    },
    "blue_chip": {
        "name": "藍籌股",
        "description": "每日成交量 > 5000 張",
        "conditions": {
            "volume_min": 5000000,
        },
    },
}


def screen_by_preset(preset: str, limit: int = 50) -> list:
    from services.finmind import client

    conditions = SCREENER_PRESETS.get(preset, {}).get("conditions", {})
    results = []
    peratio_data = client.get_peratio("2330")

    for stock_id in get_monitored_stocks():
        try:
            price_data = client.get_stock_price(stock_id, days=90)
            if not price_data:
                continue

            df = kline_to_df(price_data)
            df = compute_indicators(df)
            row = df.iloc[-1]

            if not pass_conditions(row, conditions):
                continue

            results.append({
                "stock_id": stock_id,
                "close": row["close"],
                "ma5": row.get("ma5"),
                "ma20": row.get("ma20"),
                "rsi14": row.get("rsi12"),
                "volume": row["volume"] if "volume" in row else 0,
            })
            if len(results) >= limit:
                break
        except Exception:
            continue
    return results


def pass_conditions(row: pd.Series, conditions: dict) -> bool:
    if "rsi_min" in conditions and pd.notna(row.get("rsi6")):
        if row["rsi6"] < conditions["rsi_min"]:
            return False
    if "rsi_max" in conditions and pd.notna(row.get("rsi6")):
        if row["rsi6"] > conditions["rsi_max"]:
            return False
    if conditions.get("ma20_above_ma60"):
        if pd.notna(row.get("ma20")) and pd.notna(row.get("ma60")):
            if row["ma20"] <= row["ma60"]:
                return False
    return True


def get_monitored_stocks() -> list:
    session = get_session()
    try:
        stocks = session.query(StockInfo.stock_id).limit(100).all()
        return [s[0] for s in stocks]
    except Exception:
        return ["2330", "2317", "2454", "2303", "3008"]
    finally:
        session.close()


def custom_screen(conditions: dict, stock_ids: list = None) -> list:
    if stock_ids is None:
        stock_ids = get_monitored_stocks()

    results = []
    for stock_id in stock_ids:
        try:
            price_data = client.get_stock_price(stock_id, days=90)
            if not price_data:
                continue
            df = kline_to_df(price_data)
            df = compute_indicators(df)
            row = df.iloc[-1]

            if pass_conditions(row, conditions):
                results.append({
                    "stock_id": stock_id,
                    "close": row["close"],
                    "ma5": row.get("ma5"),
                    "ma20": row.get("ma20"),
                    "rsi14": row.get("rsi12"),
                })
        except Exception:
            continue
    return results