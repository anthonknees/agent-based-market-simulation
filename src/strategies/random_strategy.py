from __future__ import annotations
import random
from typing import Optional

from order import Order, OrderType
from market import Market
from strategies.base import TradingStrategy


class RandomStrategy(TradingStrategy):
    name = "RandomStrategy"
    participation_rate = 0.30

    def __init__(self, delta: float = 2.0, qmax: int = 5) -> None:
        self.delta = delta
        self.qmax = qmax

    def generate_order(self, trader, market: Market, current_time: int, price_history: list[float]) -> Optional[Order]:
        bid, ask = market.order_book.best_bid_ask()
        mid = (bid + ask) / 2 if (bid is not None and ask is not None) else market.current_price

        side = OrderType.BUY if random.random() < 0.5 else OrderType.SELL
        price = max(1.0, mid + random.uniform(-self.delta, self.delta))
        qty = random.randint(1, self.qmax)

        return Order(side, trader.id, round(price, 2), qty, current_time)