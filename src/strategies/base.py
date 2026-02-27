from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from order import Order
from market import Market


class TradingStrategy(ABC):
    name: str = "BaseStrategy"
    participation_rate: float = 0.25

    @abstractmethod
    def generate_order(self, trader, market: Market, current_time: int, price_history: list[float]) -> Optional[Order]:
        raise NotImplementedError