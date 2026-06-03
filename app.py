from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from services.finmind import client
from services.data_sync import sync_stock_info, sync_stock_price, sync_institutional, sync_taiex, sync_all
from services.indicators import kline_to_df, compute_indicators, get_latest_indicators
from services.screener import screen_by_preset, SCREENER_PRESETS
from services.backtest import backtest_stock
from services.ai_summary import generate_summary, generate_screener_summary
from database import get_session
from models import StockPrice, StockInfo, InstitutionalTrade

app = Flask(__name__)


def normalize_kline(raw_list):
    normalized = []
    for raw in raw_list or []:
        date = raw.get("date") or raw.get("time")
        close = raw.get("close") or raw.get("Close") or raw.get("price")
        if not date or close is None:
            continue
        open_price = raw.get("open") or raw.get("Open") or close
        high = raw.get("high") or raw.get("max") or raw.get("High") or close
        low = raw.get("low") or raw.get("min") or raw.get("Low") or close
        volume = raw.get("volume") or raw.get("Trading_Volume") or 0
        trading_money = raw.get("trading_money") or raw.get("Trading_money") or raw.get("Trading_turnover") or 0
        try:
            normalized.append({
                "date": str(date),
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume or 0),
                "trading_money": float(trading_money or 0),
            })
        except (TypeError, ValueError):
            continue
    return sorted(normalized, key=lambda item: item["date"])


def format_amount(value):
    if value is None:
        return None
    if abs(value) >= 100000000:
        return f"{value / 100000000:.1f} 億"
    if abs(value) >= 10000:
        return f"{value / 10000:.1f} 萬"
    return f"{value:.0f}"


@app.route("/")
def index():
    try:
        sync_taiex(7)
    except Exception as e:
        print(f"[index] TAIEX sync error: {e}")

    index_kline = normalize_kline(client.get_stock_price("TAIEX", 90))
    if not index_kline:
        index_kline = normalize_kline(client.get_taiex(90))

    tsmc_kline = normalize_kline(client.get_stock_price("2330", 90))

    latest_index = index_kline[-1] if index_kline else None
    prev_index = index_kline[-2] if len(index_kline) >= 2 else None

    session = None
    try:
        session = get_session()
        latest_stock_date = session.query(func.max(StockPrice.date)).filter(StockPrice.stock_id != "TAIEX").scalar()
        if latest_stock_date:
            up_count = session.query(StockPrice).filter(
                StockPrice.stock_id != "TAIEX",
                StockPrice.date == latest_stock_date,
                StockPrice.spread > 0,
            ).count()
            down_count = session.query(StockPrice).filter(
                StockPrice.stock_id != "TAIEX",
                StockPrice.date == latest_stock_date,
                StockPrice.spread < 0,
            ).count()
            breadth = f"{up_count} / {down_count}" if up_count or down_count else None
        else:
            breadth = None

        latest_inst_date = session.query(func.max(InstitutionalTrade.date)).scalar()
        if latest_inst_date:
            foreign_net = session.query(func.sum(InstitutionalTrade.buy - InstitutionalTrade.sell)).filter(
                InstitutionalTrade.date == latest_inst_date,
                InstitutionalTrade.name.like("%外資%"),
            ).scalar()
        else:
            foreign_net = None
    except Exception as e:
        print(f"[index] DB read error: {e}")
        breadth = None
        foreign_net = None
    finally:
        if session:
            session.close()

    if latest_index:
        price = latest_index["close"]
        prev_price = prev_index["close"] if prev_index else price
        index_info = {
            "price": price,
            "change": round(price - prev_price, 2),
            "trading_money": format_amount(latest_index.get("trading_money")),
            "breadth": breadth,
            "foreign_net": format_amount(foreign_net),
        }
    else:
        index_info = {"price": None, "change": None, "trading_money": None, "breadth": breadth, "foreign_net": format_amount(foreign_net)}

    return render_template("index.html", index_info=index_info, index_kline=index_kline, tsmc_kline=tsmc_kline)


@app.route("/stock")
def stock():
    stock_id = request.args.get("id", "2330")

    sync_stock_info(stock_id)
    sync_stock_price(stock_id)
    sync_institutional(stock_id, 10)

    session = get_session()
    try:
        info_record = session.query(StockInfo).filter_by(stock_id=stock_id).first()
        info = {
            "stock_id": info_record.stock_id if info_record else stock_id,
            "stock_name": info_record.stock_name if info_record else "",
            "industry_category": info_record.industry_category if info_record else "",
            "type": info_record.type if info_record else "",
        }

        price_records = list(reversed(
            session.query(StockPrice)
            .filter_by(stock_id=stock_id)
            .order_by(StockPrice.date.desc())
            .limit(90)
            .all()
        ))
        kline_raw = [
            {
                "date": r.date.strftime("%Y-%m-%d") if r.date else "",
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.trading_volume,
            }
            for r in price_records
        ]

        inst_records = session.query(InstitutionalTrade).filter_by(stock_id=stock_id).order_by(InstitutionalTrade.date.desc()).limit(10).all()
        inst_raw = [
            {
                "date": r.date.strftime("%Y-%m-%d") if r.date else "",
                "name": r.name or "",
                "buy": r.buy or 0,
                "sell": r.sell or 0,
            }
            for r in inst_records
        ]
        session.close()
    except Exception as e:
        session.close()
        print(f"[stock] DB read error: {e}")
        info = {"stock_id": stock_id, "stock_name": "", "industry_category": "", "type": ""}
        kline_raw = []
        inst_raw = []

    df = kline_to_df(kline_raw)
    if not df.empty:
        df = compute_indicators(df)
        indicators = get_latest_indicators(df)
    else:
        indicators = {}

    ai_summary = generate_summary(stock_id, info.get("stock_name", stock_id), kline_raw, indicators)

    return render_template("stock.html", info=info, kline=kline_raw, institutional=inst_raw, indicators=indicators, ai_summary=ai_summary)


@app.route("/indicator")
def indicator_page():
    stock_id = request.args.get("id", "2330")

    sync_stock_price(stock_id, 180)

    session = get_session()
    try:
        price_records = session.query(StockPrice).filter_by(stock_id=stock_id).order_by(StockPrice.date.desc()).limit(180).all()
        kline_raw = [
            {
                "date": r.date.strftime("%Y-%m-%d") if r.date else "",
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.trading_volume,
            }
            for r in price_records
        ]
        session.close()
    except Exception as e:
        session.close()
        print(f"[indicator] DB read error: {e}")
        kline_raw = []

    df = kline_to_df(kline_raw)
    df = compute_indicators(df)
    return render_template("indicator.html", kline=kline_raw, df=df.to_dict("records") if not df.empty else [], stock_id=stock_id)


@app.route("/screener", methods=["GET", "POST"])
def screener_page():
    preset = request.args.get("preset", "momentum")
    results = screen_by_preset(preset, limit=50)
    ai_summary = generate_screener_summary(results, SCREENER_PRESETS.get(preset, {}).get("name", preset))
    presets = SCREENER_PRESETS
    return render_template("screener.html", results=results, presets=presets, current_preset=preset, ai_summary=ai_summary)


@app.route("/backtest", methods=["GET", "POST"])
def backtest_page():
    stock_id = request.args.get("stock_id", "2330")
    strategy = request.args.get("strategy", "ma_cross")
    result = None

    if request.args.get("run") == "1":
        result = backtest_stock(stock_id, strategy, days=365)

    return render_template("backtest.html", stock_id=stock_id, strategy=strategy, result=result)


@app.route("/sync", methods=["POST"])
def sync_data():
    stock_ids = request.json.get("stock_ids", ["2330", "2317", "2454"]) if request.is_json else ["2330", "2317", "2454"]
    results = sync_all(stock_ids)
    return jsonify({"status": "ok", "results": results})


@app.route("/api/kline/<stock_id>")
def api_kline(stock_id):
    days = request.args.get("days", 90, type=int)
    data = client.get_stock_price(stock_id, days)
    return jsonify(data)


@app.route("/api/indicators/<stock_id>")
def api_indicators(stock_id):
    kline_raw = client.get_stock_price(stock_id, 180)
    df = kline_to_df(kline_raw)
    df = compute_indicators(df)
    indicators = get_latest_indicators(df)
    return jsonify(indicators or {})


@app.route("/api/taiex")
def api_taiex():
    data = client.get_taiex(7)
    return jsonify(data[-1] if data else {})


@app.route("/api/institutional/<stock_id>")
def api_inst(stock_id):
    days = request.args.get("days", 10, type=int)
    data = client.get_institutional(stock_id, days)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
