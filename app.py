from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
from os import getenv
from dotenv import load_dotenv

load_dotenv()
token = getenv('FINMIND_TOKEN')

app = Flask(__name__)

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"
HEADERS = {"Authorization": f"Bearer {token}"}


def getTaiwanWeightedIndex():
    """Get Taiwan Weighted Index data from FinMind v4 API."""
    params = {
        "dataset": "TaiwanStockTotalReturnIndex",
        "data_id": "TAIEX",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d"),
    }
    resp = requests.get(FINMIND_API, params=params, headers=HEADERS, timeout=10)
    if resp.status_code == 200:
        raw = resp.json().get("data", [])
        if raw and len(raw) >= 1:
            latest = raw[-1]
            price = float(latest.get("price", 0))
            # Use previous day's price for change
            if len(raw) >= 2:
                prev_price = float(raw[-2].get("price", price))
            else:
                prev_price = price
            return {
                "index": round(price, 2),
                "change": round(price - prev_price, 2),
                "volume": 0,
                "up_count": 0,
                "down_count": 0,
                "foreign_net": 0,
            }
    return {"error": "無法獲取資料"}


def get_kline_data(stock_id="2330", days=30):
    """Get K-line (OHLC) data for a stock from FinMind v4 API."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    resp = requests.get(FINMIND_API, params=params, headers=HEADERS, timeout=10)
    if resp.status_code == 200:
        raw = resp.json().get("data", [])
        if raw:
            data = []
            for r in raw:
                data.append({
                    "time": r.get("date", ""),
                    "open": float(r.get("open", 0)),
                    "high": float(r.get("max", 0)),
                    "low": float(r.get("min", 0)),
                    "close": float(r.get("close", 0)),
                    "volume": float(r.get("Trading_Volume", 0)),
                })
            return data
    return []


def get_stock_info(stock_id):
    """Get stock basic info from FinMind v4 API."""
    params = {
        "dataset": "TaiwanStockInfo",
        "data_id": stock_id,
    }
    resp = requests.get(FINMIND_API, params=params, headers=HEADERS, timeout=10)
    if resp.status_code == 200:
        raw = resp.json().get("data", [])
        if raw:
            info = raw[0]
            return {
                "stock_id": info.get("stock_id", stock_id),
                "stock_name": info.get("stock_name", f"股票{stock_id}"),
                "industry_category": info.get("industry_category", "其他"),
                "type": info.get("type", ""),
            }
    return {"error": "無法獲取資料"}


def get_institutional_trades(stock_id):
    """Get institutional investor buy/sell data from FinMind v4 API."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    params = {
        "dataset": "InstitutionalInvestorsBuySell",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    resp = requests.get(FINMIND_API, params=params, headers=HEADERS, timeout=10)
    if resp.status_code == 200:
        raw = resp.json().get("data", [])
        if raw:
            result = []
            for r in raw:
                result.append({
                    "date": r.get("date", ""),
                    "buy": float(r.get("buy", 0)),
                    "sell": float(r.get("sell", 0)),
                    "name": r.get("name", ""),
                })
            return result[:10]
    return []


@app.route("/")
def index():
    index_data = getTaiwanWeightedIndex()
    weighted_kline = get_kline_data("TAIEX", 60)
    tsmc_kline = get_kline_data("2330", 60)
    return render_template(
        "index.html",
        index_data=index_data,
        weighted_kline=weighted_kline,
        tsmc_kline=tsmc_kline,
    )


@app.route("/stock")
def stock():
    stock_id = request.args.get("id", "2330")
    info = get_stock_info(stock_id)
    kline = get_kline_data(stock_id, 60)
    trades = get_institutional_trades(stock_id)
    return render_template("stock.html", info=info, kline=kline, trades=trades)


@app.route("/api/kline/<stock_id>")
def api_kline(stock_id):
    days = request.args.get("days", 60, type=int)
    data = get_kline_data(stock_id, days)
    return jsonify(data)


@app.route("/api/index")
def api_index():
    data = getTaiwanWeightedIndex()
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
