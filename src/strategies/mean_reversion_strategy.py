from __future__ import annotations
import random
from typing import Optional

from order import Order, OrderType
from market import Market
from strategies.base import TradingStrategy


class MeanReversionStrategy(TradingStrategy):
    name = "MeanReversionStrategy"
    participation_rate = 0.25

    def __init__(self, window: int = 20, theta: float = 1.0, kappa: float = 0.5, qmax: int = 4) -> None:
        self.window = window
        self.theta = theta
        self.kappa = kappa
        self.qmax = qmax

    def generate_order(self, trader, market: Market, current_time: int, price_history: list[float]) -> Optional[Order]:
        if len(price_history) < self.window:
            return None

        mu = sum(price_history[-self.window:]) / self.window
        d = price_history[-1] - mu
        if abs(d) < self.theta:
            return None

        bid, ask = market.order_book.best_bid_ask()
        mid = (bid + ask) / 2 if (bid is not None and ask is not None) else market.current_price

        side = OrderType.SELL if d > 0 else OrderType.BUY
        price = max(1.0, mid + (-self.kappa if side == OrderType.SELL else self.kappa))
        qty = random.randint(1, self.qmax)

        return Order(side, trader.id, round(price, 2), qty, current_time)