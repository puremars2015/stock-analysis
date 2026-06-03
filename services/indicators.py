import pandas as pd
from typing import List, Tuple, Optional


def calculate_ma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dem = dif.ewm(span=signal, adjust=False).mean()
    oscil = dif - dem
    return dif, dem, oscil


def calculate_kd(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 9) -> Tuple[pd.Series, pd.Series]:
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low + 1e-9) * 100
    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    d = k.ewm(alpha=1/3, adjust=False).mean()
    return k, d


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ma5"] = calculate_ma(df["close"], 5)
    df["ma10"] = calculate_ma(df["close"], 10)
    df["ma20"] = calculate_ma(df["close"], 20)
    df["ma60"] = calculate_ma(df["close"], 60)
    df["rsi6"] = calculate_rsi(df["close"], 6)
    df["rsi12"] = calculate_rsi(df["close"], 12)
    df["rsi24"] = calculate_rsi(df["close"], 24)
    df["macd_dif"], df["macd_dem"], df["macd_oscil"] = calculate_macd(df["close"])
    df["k_value"], df["d_value"] = calculate_kd(df["high"], df["low"], df["close"])
    return df


def get_latest_indicators(df: pd.DataFrame) -> Optional[dict]:
    if df.empty or len(df) < 60:
        return None
    row = df.iloc[-1]
    return {
        "ma5": round(row["ma5"], 2) if pd.notna(row["ma5"]) else None,
        "ma10": round(row["ma10"], 2) if pd.notna(row["ma10"]) else None,
        "ma20": round(row["ma20"], 2) if pd.notna(row["ma20"]) else None,
        "ma60": round(row["ma60"], 2) if pd.notna(row["ma60"]) else None,
        "rsi6": round(row["rsi6"], 2) if pd.notna(row["rsi6"]) else None,
        "rsi12": round(row["rsi12"], 2) if pd.notna(row["rsi12"]) else None,
        "rsi24": round(row["rsi24"], 2) if pd.notna(row["rsi24"]) else None,
        "macd_dif": round(row["macd_dif"], 3) if pd.notna(row["macd_dif"]) else None,
        "macd_dem": round(row["macd_dem"], 3) if pd.notna(row["macd_dem"]) else None,
        "macd_oscil": round(row["macd_oscil"], 3) if pd.notna(row["macd_oscil"]) else None,
        "k_value": round(row["k_value"], 2) if pd.notna(row["k_value"]) else None,
        "d_value": round(row["d_value"], 2) if pd.notna(row["d_value"]) else None,
    }


def kline_to_df(kline_data: List[dict]) -> pd.DataFrame:
    if not kline_data:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(kline_data)
    if "time" in df.columns:
        df = df.rename(columns={"time": "date"})
    rename_map = {"Open": "open", "max": "high", "min": "low", "Close": "close", "Trading_Volume": "volume"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df