from datetime import datetime, date
from time import sleep
from database import get_session
from models import StockInfo, StockPrice, InstitutionalTrade, TAIEXData, TaiwanStockTotalReturnIndex
from services.finmind import client


SYNC_REQUEST_DELAY_SECONDS = 0.5


def parse_date(s: str):
    if isinstance(s, date):
        return s
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    return int(_to_float(value, default))


def _rate_limit_sleep():
    sleep(SYNC_REQUEST_DELAY_SECONDS)


def _upsert_stock_info_records(session, raw_list):
    count = 0
    for raw in raw_list:
        stock_id = str(raw.get("stock_id") or "").strip()
        if not stock_id:
            continue

        info = session.query(StockInfo).filter_by(stock_id=stock_id).first()
        if info:
            info.stock_name = raw.get("stock_name", info.stock_name)
            info.industry_category = raw.get("industry_category", info.industry_category)
            info.type = raw.get("type", info.type)
            info.listing_date = parse_date(raw.get("date", "")) or info.listing_date
            info.updated_at = datetime.utcnow()
        else:
            session.add(StockInfo(
                stock_id=stock_id,
                stock_name=raw.get("stock_name", f"股票{stock_id}"),
                industry_category=raw.get("industry_category", "其他"),
                type=raw.get("type", ""),
                listing_date=parse_date(raw.get("date", "")),
            ))
            count += 1
    return count


def _latest_market_value_by_stock(raw_list):
    latest_date = None
    latest_rows = []

    for raw in raw_list:
        d = parse_date(raw.get("date", ""))
        if not d:
            continue
        if latest_date is None or d > latest_date:
            latest_date = d
            latest_rows = [raw]
        elif d == latest_date:
            latest_rows.append(raw)

    market_values = {}
    for raw in latest_rows:
        stock_id = str(raw.get("stock_id") or "").strip()
        value = _to_float(
            raw.get("market_value")
            or raw.get("MarketValue")
            or raw.get("market_capital")
            or raw.get("market_cap")
        )
        if stock_id and value > 0:
            market_values[stock_id] = value
    return market_values


def _top_stock_ids_by_market_value(stock_info_list, market_value_list, limit=50):
    market_values = _latest_market_value_by_stock(market_value_list)
    if market_values:
        return [
            stock_id
            for stock_id, _ in sorted(market_values.items(), key=lambda item: item[1], reverse=True)[:limit]
        ]

    candidates = []
    for raw in stock_info_list:
        stock_id = str(raw.get("stock_id") or "").strip()
        value = _to_float(
            raw.get("market_value")
            or raw.get("capital")
            or raw.get("stock_capital")
            or raw.get("paid_in_capital")
        )
        if stock_id and value > 0:
            candidates.append((stock_id, value))

    if candidates:
        return [stock_id for stock_id, _ in sorted(candidates, key=lambda item: item[1], reverse=True)[:limit]]

    # FinMind may not expose market value for all tokens/plans. Keep the sync usable,
    # but make the fallback deterministic instead of failing after StockInfo sync.
    stock_ids = [str(raw.get("stock_id") or "").strip() for raw in stock_info_list]
    return [stock_id for stock_id in stock_ids if stock_id][:limit]


def sync_stock_info(stock_id: str):
    session = get_session()
    try:
        raw = client.get_stock_info(stock_id)
        if not raw:
            return False
        info = session.query(StockInfo).filter_by(stock_id=stock_id).first()
        if info:
            info.stock_name = raw.get("stock_name", info.stock_name)
            info.industry_category = raw.get("industry_category", info.industry_category)
            info.type = raw.get("type", info.type)
            info.updated_at = datetime.utcnow()
        else:
            info = StockInfo(
                stock_id=stock_id,
                stock_name=raw.get("stock_name", f"股票{stock_id}"),
                industry_category=raw.get("industry_category", "其他"),
                type=raw.get("type", ""),
                listing_date=parse_date(raw.get("date", "")),
            )
            session.add(info)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"[sync] stock_info error: {e}")
        return False
    finally:
        session.close()


def sync_stock_price(stock_id: str, days: int = 90):
    session = get_session()
    try:
        raw_list = client.get_stock_price(stock_id, days)
        if not raw_list:
            return 0
        count = 0
        for raw in raw_list:
            d = parse_date(raw.get("date", ""))
            if not d:
                continue
            existing = session.query(StockPrice).filter_by(stock_id=stock_id, date=d).first()
            if existing:
                existing.open = _to_float(raw.get("open", 0))
                existing.high = _to_float(raw.get("max", 0))
                existing.low = _to_float(raw.get("min", 0))
                existing.close = _to_float(raw.get("close", 0))
                existing.spread = _to_float(raw.get("spread", 0))
                existing.trading_volume = _to_int(raw.get("Trading_Volume", 0))
                existing.trading_turnover = _to_int(raw.get("Trading_turnover", 0))
            else:
                session.add(StockPrice(
                    stock_id=stock_id,
                    date=d,
                    open=_to_float(raw.get("open", 0)),
                    high=_to_float(raw.get("max", 0)),
                    low=_to_float(raw.get("min", 0)),
                    close=_to_float(raw.get("close", 0)),
                    spread=_to_float(raw.get("spread", 0)),
                    trading_volume=_to_int(raw.get("Trading_Volume", 0)),
                    trading_turnover=_to_int(raw.get("Trading_turnover", 0)),
                ))
                count += 1
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        print(f"[sync] stock_price error: {e}")
        return 0
    finally:
        session.close()


def sync_institutional(stock_id: str, days: int = 10):
    session = get_session()
    try:
        raw_list = client.get_institutional(stock_id, days)
        print(f"[sync] institutional raw_list count: {len(raw_list)} for {stock_id}")
        if not raw_list:
            return 0
        count = 0
        for raw in raw_list:
            d = parse_date(raw.get("date", ""))
            if not d:
                continue
            name = raw.get("name", "")
            existing = session.query(InstitutionalTrade).filter_by(
                stock_id=stock_id, date=d, name=name
            ).first()
            if existing:
                # Update existing
                existing.buy = _to_int(raw.get("buy", 0))
                existing.sell = _to_int(raw.get("sell", 0))
            else:
                session.add(InstitutionalTrade(
                    stock_id=stock_id,
                    date=d,
                    name=name,
                    buy=_to_int(raw.get("buy", 0)),
                    sell=_to_int(raw.get("sell", 0)),
                ))
                count += 1
        session.commit()
        print(f"[sync] institutional added: {count} for {stock_id}")
        return count
    except Exception as e:
        session.rollback()
        print(f"[sync] institutional error: {e}")
        return 0
    finally:
        session.close()


def sync_taiex(days: int = 7):
    session = get_session()
    try:
        raw_list = client.get_taiex(days)
        if not raw_list:
            return 0
        count = 0
        for raw in raw_list:
            d = parse_date(raw.get("date", ""))
            if not d:
                continue
            existing = session.query(TAIEXData).filter_by(date=d).first()
            if not existing:
                session.add(TAIEXData(
                    date=d,
                    price=float(raw.get("price", 0)),
                    return_rate=float(raw.get("return_rate", 0)),
                ))
                count += 1
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        print(f"[sync] taiex error: {e}")
        return 0
    finally:
        session.close()


def sync_all(stock_ids: list):
    results = {}
    for sid in stock_ids:
        sync_stock_info(sid)
        results[f"{sid}_price"] = sync_stock_price(sid)
        results[f"{sid}_inst"] = sync_institutional(sid)
    sync_taiex()
    return results


def sync_all_market_data(top_n: int = 50):
    results = {
        "stock_info": 0,
        "top_stock_ids": [],
        "stock_price": {},
        "institutional_trade": {},
    }

    session = get_session()
    try:
        stock_info_list = client.get_all_stock_info()
        _rate_limit_sleep()
        if not stock_info_list:
            return {**results, "status": "no_stock_info"}

        results["stock_info"] = _upsert_stock_info_records(session, stock_info_list)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[sync-all] stock_info error: {e}")
        return {**results, "status": "stock_info_error", "error": str(e)}
    finally:
        session.close()

    try:
        market_value_list = client.get_market_value(7)
        _rate_limit_sleep()
    except Exception as e:
        print(f"[sync-all] market_value error: {e}")
        market_value_list = []

    top_stock_ids = _top_stock_ids_by_market_value(stock_info_list, market_value_list, top_n)
    results["top_stock_ids"] = top_stock_ids

    for stock_id in top_stock_ids:
        results["stock_price"][stock_id] = sync_stock_price(stock_id, 90)
        _rate_limit_sleep()
        results["institutional_trade"][stock_id] = sync_institutional(stock_id, 30)
        _rate_limit_sleep()

    return {**results, "status": "ok"}
