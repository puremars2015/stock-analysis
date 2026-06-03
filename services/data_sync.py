from datetime import datetime, date
from database import get_session
from models import StockInfo, StockPrice, InstitutionalTrade, TAIEXData, TaiwanStockTotalReturnIndex
from services.finmind import client


def parse_date(s: str):
    if isinstance(s, date):
        return s
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


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
                existing.open = float(raw.get("open", 0))
                existing.high = float(raw.get("max", 0))
                existing.low = float(raw.get("min", 0))
                existing.close = float(raw.get("close", 0))
                existing.spread = float(raw.get("spread", 0))
                existing.trading_volume = int(float(raw.get("Trading_Volume", 0)))
                existing.trading_turnover = int(float(raw.get("Trading_turnover", 0)))
            else:
                session.add(StockPrice(
                    stock_id=stock_id,
                    date=d,
                    open=float(raw.get("open", 0)),
                    high=float(raw.get("max", 0)),
                    low=float(raw.get("min", 0)),
                    close=float(raw.get("close", 0)),
                    spread=float(raw.get("spread", 0)),
                    trading_volume=int(float(raw.get("Trading_Volume", 0))),
                    trading_turnover=int(float(raw.get("Trading_turnover", 0))),
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
                existing.buy = int(float(raw.get("buy", 0)))
                existing.sell = int(float(raw.get("sell", 0)))
            else:
                session.add(InstitutionalTrade(
                    stock_id=stock_id,
                    date=d,
                    name=name,
                    buy=int(float(raw.get("buy", 0))),
                    sell=int(float(raw.get("sell", 0))),
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