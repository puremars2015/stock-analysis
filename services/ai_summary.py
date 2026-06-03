import os
from typing import Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def generate_summary(stock_id: str, stock_name: str, price_data: list, indicators: dict) -> str:
    if not OPENAI_API_KEY:
        return _fallback_summary(stock_id, stock_name, indicators)

    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        recent = price_data[-5:] if len(price_data) >= 5 else price_data
        price_str = ", ".join([f"${p.get('close', 0):.2f}" for p in recent])

        prompt = f"""分析股票 {stock_id} ({stock_name})：
最新收盤價：{price_str}
技術指標：
- MA5: {indicators.get('ma5')}
- MA20: {indicators.get('ma20')}
- RSI(6): {indicators.get('rsi6')}
- MACD DIF: {indicators.get('macd_dif')}
- MACD DEM: {indicators.get('macd_dem')}
- K: {indicators.get('k_value')}
- D: {indicators.get('d_value')}

請用繁體中文提供簡短的投資分析摘要（3-5句）。"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e:
        return _fallback_summary(stock_id, stock_name, indicators)


def generate_screener_summary(results: list, preset: str) -> str:
    if not OPENAI_API_KEY:
        return f"找到 {len(results)} 檔符合條件的股票"

    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        stock_list = "\n".join([f"- {r['stock_id']}: 收盤價 ${r.get('close', 0):.2f}" for r in results[:10]])

        prompt = f"""根據以下篩選結果，提供繁體中文分析摘要：
篩選條件：{preset}
符合股票：
{stock_list}

請用繁體中文提供簡短的分析結論（3句以內）。"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message.content
    except Exception:
        return f"找到 {len(results)} 檔符合條件的股票"


def _fallback_summary(stock_id: str, stock_name: str, indicators: dict) -> str:
    parts = []
    rsi = indicators.get("rsi6")
    if rsi:
        if rsi > 70:
            parts.append("RSI 偏高，可能存在超買風險")
        elif rsi < 30:
            parts.append("RSI 偏低，可能存在超賣機會")
        else:
            parts.append(f"RSI 為 {rsi:.1f}，區間正常")

    ma5 = indicators.get("ma5")
    ma20 = indicators.get("ma20")
    if ma5 and ma20:
        if ma5 > ma20:
            parts.append("短期均線優於長期均線，呈多頭排列")
        else:
            parts.append("短期均線低於長期均線，需謹慎")

    k = indicators.get("k_value")
    d = indicators.get("d_value")
    if k and d:
        if k > 80 and d > 80:
            parts.append("KD 高檔，可能面臨回檔壓力")
        elif k < 20 and d < 20:
            parts.append("KD 低檔，可能存在反彈機會")

    return f"{stock_name} ({stock_id})：" + "；".join(parts) if parts else f"{stock_name} ({stock_id}) 技術面無明顯訊號"