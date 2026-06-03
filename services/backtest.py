import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from database import get_session
from models import StockPrice, BacktestResult
from services.indicators import kline_to_df, compute_indicators


class BacktestEngine:
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position = 0
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []

    def reset(self):
        self.cash = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []

    def buy(self, date, price, shares=None):
        if shares is None:
            shares = int(self.cash / price)
        cost = shares * price * 1.425 / 1000
        if self.cash >= cost:
            self.cash -= cost
            self.position += shares
            self.trades.append({"date": date, "action": "buy", "price": price, "shares": shares})
            return True
        return False

    def sell(self, date, price, shares=None):
        if shares is None:
            shares = self.position
        if self.position >= shares:
            revenue = shares * price * (1 - 1.425 / 1000)
            self.cash += revenue
            self.position -= shares
            self.trades.append({"date": date, "action": "sell", "price": price, "shares": shares})
            return True
        return False

    @property
    def equity(self) -> float:
        return self.cash + self.position * self.equity_curve[-1] if self.equity_curve else self.cash

    def run_ma_cross(self, df: pd.DataFrame, fast: int = 5, slow: int = 20) -> Dict:
        self.reset()
        df = df.copy().reset_index(drop=True)
        for i in range(slow, len(df)):
            row = df.iloc[i]
            ma_fast = df.iloc[i - fast + 1:i + 1]["close"].mean()
            ma_slow = df.iloc[i - slow + 1:i + 1]["close"].mean()
            ma_fast_prev = df.iloc[i - fast]["close"] if i >= fast else None
            ma_slow_prev = df.iloc[i - slow]["close"] if i >= slow else None

            if ma_fast_prev is not None and ma_slow_prev is not None:
                if ma_fast_prev < ma_slow_prev and ma_fast > ma_slow:
                    self.buy(row["date"], row["close"])
                elif ma_fast_prev > ma_slow_prev and ma_fast < ma_slow:
                    self.sell(row["date"], row["close"])

        final_equity = self.cash + self.position * df.iloc[-1]["close"]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        max_drawdown = self._calc_max_drawdown(df)
        win_rate = self._calc_win_rate()

        return {
            "strategy": f"MA{fast}_MA{slow}",
            "total_return": round(total_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": len(self.trades),
            "final_equity": round(final_equity, 2),
        }

    def run_rsi(self, df: pd.DataFrame, period: int = 14, lower: int = 30, upper: int = 70) -> Dict:
        self.reset()
        df = compute_indicators(df).reset_index(drop=True)
        in_position = False

        for i in range(period, len(df)):
            row = df.iloc[i]
            rsi = row.get("rsi6")
            if pd.isna(rsi):
                continue

            if not in_position and rsi < lower:
                self.buy(row["date"], row["close"])
                in_position = True
            elif in_position and rsi > upper:
                self.sell(row["date"], row["close"])
                in_position = False

        if self.position > 0:
            self.sell(df.iloc[-1]["date"], df.iloc[-1]["close"])

        final_equity = self.cash + self.position * df.iloc[-1]["close"]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100

        return {
            "strategy": f"RSI({period},{lower},{upper})",
            "total_return": round(total_return, 2),
            "max_drawdown": round(self._calc_max_drawdown(df), 2),
            "win_rate": round(self._calc_win_rate(), 2),
            "total_trades": len(self.trades),
            "final_equity": round(final_equity, 2),
        }

    def _calc_max_drawdown(self, df: pd.DataFrame) -> float:
        peak = self.initial_capital
        max_dd = 0
        equity = self.initial_capital
        for i, row in df.iterrows():
            if self.trades:
                last_trade = self.trades[-1]
                equity = self.cash
            max_dd = max(max_dd, (peak - equity) / peak * 100)
            peak = max(peak, equity)
        return max_dd

    def _calc_win_rate(self) -> float:
        if not self.trades:
            return 0
        sells = [t for t in self.trades if t["action"] == "sell"]
        if len(sells) < 2:
            return 0
        wins = 0
        for i in range(1, len(sells)):
            prev_buy = sells[i - 1]["price"]
            curr_sell = sells[i]["price"]
            if curr_sell > prev_buy:
                wins += 1
        return wins / (len(sells) - 1) * 100

    def save_result(self, name: str, stock_id: str, start_date: date, end_date: date, result: Dict):
        session = get_session()
        try:
            br = BacktestResult(
                name=name,
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date,
                strategy=result.get("strategy", ""),
                total_return=result.get("total_return", 0),
                max_drawdown=result.get("max_drawdown", 0),
                win_rate=result.get("win_rate", 0),
                sharpe_ratio=0,
            )
            session.add(br)
            session.commit()
            return br.id
        except Exception as e:
            session.rollback()
            print(f"[backtest] save error: {e}")
            return None
        finally:
            session.close()


def backtest_stock(stock_id: str, strategy: str = "ma_cross", days: int = 365) -> Dict:
    from services.finmind import client
    from models import StockPrice

    session = get_session()
    try:
        prices = session.query(StockPrice).filter(
            StockPrice.stock_id == stock_id
        ).order_by(StockPrice.date.desc()).limit(days).all()

        if prices:
            kline = [{"date": p.date, "open": p.open, "high": p.high,
                      "low": p.low, "close": p.close, "volume": p.trading_volume} for p in reversed(prices)]
        else:
            raw = client.get_stock_price(stock_id, days)
            kline = raw

        if not kline:
            return {"error": "No data"}

        df = kline_to_df(kline)
        engine = BacktestEngine()

        if strategy == "ma_cross":
            result = engine.run_ma_cross(df)
        elif strategy == "rsi":
            result = engine.run_rsi(df)
        else:
            result = engine.run_ma_cross(df)

        start_date = df.iloc[0]["date"].date() if not df.empty else None
        end_date = df.iloc[-1]["date"].date() if not df.empty else None
        if start_date and end_date:
            engine.save_result(f"{stock_id}_{strategy}", stock_id, start_date, end_date, result)

        return result
    finally:
        session.close()