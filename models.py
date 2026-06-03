from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StockInfo(Base):
    __tablename__ = "stock_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), unique=True, nullable=False, index=True)
    stock_name = Column(String(100))
    industry_category = Column(String(100))
    type = Column(String(50))
    listing_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockPrice(Base):
    __tablename__ = "stock_price"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    spread = Column(Float)
    trading_volume = Column(Integer)
    trading_turnover = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_stock_price_stock_date", "stock_id", "date", unique=True),
    )


class InstitutionalTrade(Base):
    __tablename__ = "institutional_trade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    name = Column(String(100))
    buy = Column(Integer)
    sell = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_inst_stock_date_name", "stock_id", "date", "name", unique=True),
    )


class TAIEXData(Base):
    __tablename__ = "taiex_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    price = Column(Float)
    return_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaiwanStockTotalReturnIndex(Base):
    __tablename__ = "taiwan_total_return_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockIndicator(Base):
    __tablename__ = "stock_indicator"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    ma5 = Column(Float)
    ma10 = Column(Float)
    ma20 = Column(Float)
    ma60 = Column(Float)
    rsi6 = Column(Float)
    rsi12 = Column(Float)
    rsi24 = Column(Float)
    macd_dif = Column(Float)
    macd_dem = Column(Float)
    macd_oscil = Column(Float)
    k_value = Column(Float)
    d_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_indicator_stock_date", "stock_id", "date", unique=True),
    )


class ScreenerCondition(Base):
    __tablename__ = "screener_condition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    conditions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BacktestResult(Base):
    __tablename__ = "backtest_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    stock_id = Column(String(10))
    start_date = Column(Date)
    end_date = Column(Date)
    strategy = Column(Text)
    total_return = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    sharpe_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)