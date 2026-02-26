from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Optional

from order import Order, OrderType
from market import Market
from strategies.base import TradingStrategy


@dataclass
class Trader:
    id: int
    capital: float
    inventory: int
    strategy: TradingStrategy

    def decide_action(self, market: Market, current_time: int, price_history: list[float]) -> None:
        # stochastic participation
        if random.random() > self.strategy.participation_rate:
            return

        order: Optional[Order] = self.strategy.generate_order(self, market, current_time, price_history)
        if order is None:
            return

        # enforce assumptions: no negative cash, no short-selling
        if order.order_type == OrderType.BUY:
            if order.price * order.quantity > self.capital:
                return
        else:
            if order.quantity > self.inventory:
                return

        market.order_book.add_order(order)