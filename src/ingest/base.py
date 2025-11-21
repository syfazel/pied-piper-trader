# src/ingest/base.py
from abc import ABC, abstractmethod
import pandas as pd
import aiohttp

class BaseConnector(ABC):
    """
    کلاس انتزاعی برای تمام صرافی‌ها.
    همه صرافی‌ها مجبورند متد fetch_ohlcv را داشته باشند.
    """
    def __init__(self, name: str):
        self.name = name
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """
        باید داده‌ها را بگیرد و یک DataFrame استاندارد برگرداند.
        """
        pass