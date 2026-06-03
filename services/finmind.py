import os
import requests
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"


class FinMindClient:
    def __init__(self):
        self.token = os.getenv("FINMIND_TOKEN", "")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.base_url = FINMIND_API

    def _refresh_token(self):
        """Refresh token from environment in case it changed."""
        current = os.getenv("FINMIND_TOKEN", "")
        if current and current != self.token:
            self.token = current
            self.headers = {"Authorization": f"Bearer {self.token}"}

    def _request(self, dataset: str, data_id: Optional[str] = None,
                 start_date: Optional[str] = None, end_date: Optional[str] = None,
                 params: Optional[dict] = None) -> list:
        self._refresh_token()
        payload = {"dataset": dataset}
        if data_id:
            payload["data_id"] = data_id
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        if params:
            payload.update(params)

        resp = requests.get(self.base_url, params=payload, headers=self.headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        return []

    def get_stock_info(self, stock_id: str) -> Optional[dict]:
        data = self._request("TaiwanStockInfo", data_id=stock_id)
        return data[0] if data else None

    def get_all_stock_info(self) -> list:
        return self._request("TaiwanStockInfo")

    def get_stock_price(self, stock_id: str, days: int = 90) -> list:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self._request("TaiwanStockPrice", data_id=stock_id, start_date=start, end_date=end)

    def get_taiex(self, days: int = 7) -> list:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self._request("TaiwanStockTotalReturnIndex", data_id="TAIEX", start_date=start, end_date=end)

    def get_institutional(self, stock_id: str, days: int = 10) -> list:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self._request("TaiwanStockInstitutionalInvestorsBuySell", data_id=stock_id, start_date=start, end_date=end)

    def get_market_value(self, days: int = 7) -> list:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self._request("TaiwanStockMarketValue", start_date=start, end_date=end)

    def get_broad_index(self, index_id: str = "TAIEX", days: int = 7) -> list:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self._request("TaiwanWeightedIndex", data_id=index_id, start_date=start, end_date=end)

    def get_peratio(self, stock_id: str) -> list:
        return self._request("TaiwanStockPERatio", data_id=stock_id)

    def get_shareholding(self, stock_id: str, days: int = 90) -> list:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self._request("TaiwanStockShareholding", data_id=stock_id, start_date=start, end_date=end)

    def search_stock(self, stock_id: str) -> list:
        return self._request("TaiwanStockInfo", data_id=stock_id)


client = FinMindClient()
