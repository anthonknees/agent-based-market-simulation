from __future__ import annotations
import random
from typing import Optional

from order import Order, OrderType
from market import Market
from strategies.base import TradingStrategy


class MomentumStrategy(TradingStrategy):
    name = "MomentumStrategy"
    participation_rate = 0.25

    def __init__(self, lookback: int = 10, theta: float = 1.0, kappa: float = 0.5, qmax: int = 4) -> None:
        self.lookback = lookback
        self.theta = theta
        self.kappa = kappa
        self.qmax = qmax

    def generate_order(self, trader, market: Market, current_time: int, price_history: list[float]) -> Optional[Order]:
        if len(price_history) <= self.lookback:
            return None

        m = price_history[-1] - price_history[-1 - self.lookback]
        if abs(m) < self.theta:
            return None

        bid, ask = market.order_book.best_bid_ask()
        mid = (bid + ask) / 2 if (bid is not None and ask is not None) else market.current_price

        side = OrderType.BUY if m > 0 else OrderType.SELL
        price = max(1.0, mid + (self.kappa if side == OrderType.BUY else -self.kappa))
        qty = random.randint(1, self.qmax)

        return Order(side, trader.id, round(price, 2), qty, current_time)