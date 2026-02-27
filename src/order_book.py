from __future__ import annotations

import heapq
import itertools
from typing import Dict, List, Optional, Tuple

from order import Order, OrderType


class OrderBook:
    """
    Heap-based limit order book with price-time priority.

    Buy book:  max-heap by price, then earliest time (implemented using negative price)
    Sell book: min-heap by price, then earliest time
    """

    def __init__(self) -> None:
        self._buy: List[Tuple[float, int, int, Order]] = []   # (-price, time, seq, order)
        self._sell: List[Tuple[float, int, int, Order]] = []  # ( price, time, seq, order)
        self.trader_registry: Dict[int, object] = {}
        self._seq = itertools.count()

    def register_traders(self, traders: List[object]) -> None:
        self.trader_registry = {t.id: t for t in traders}

    def add_order(self, order: Order) -> None:
        seq = next(self._seq)
        if order.order_type == OrderType.BUY:
            heapq.heappush(self._buy, (-order.price, order.timestamp, seq, order))
        else:
            heapq.heappush(self._sell, (order.price, order.timestamp, seq, order))

    def best_bid_ask(self) -> Tuple[Optional[float], Optional[float]]:
        bid = -self._buy[0][0] if self._buy else None
        ask = self._sell[0][0] if self._sell else None
        return bid, ask

    def match_orders(self) -> List[dict]:
        """
        Match while best_bid >= best_ask.
        Trade price rule: execute at best ask price.
        Partial fills are reinserted with the original timestamp.
        """
        trades: List[dict] = []

        while self._buy and self._sell:
            best_bid = -self._buy[0][0]
            best_ask = self._sell[0][0]

            if best_bid < best_ask:
                break

            _, _, _, buy_order = heapq.heappop(self._buy)
            _, _, _, sell_order = heapq.heappop(self._sell)

            qty = min(buy_order.quantity, sell_order.quantity)
            trade_price = best_ask

            buyer = self.trader_registry.get(buy_order.trader_id)
            seller = self.trader_registry.get(sell_order.trader_id)
            if buyer is None or seller is None:
                continue

            trades.append({
                "buyer": buyer,
                "seller": seller,
                "price": trade_price,
                "quantity": qty
            })

            if buy_order.quantity > qty:
                self.add_order(Order(
                    order_type=OrderType.BUY,
                    trader_id=buy_order.trader_id,
                    price=buy_order.price,
                    quantity=buy_order.quantity - qty,
                    timestamp=buy_order.timestamp
                ))

            if sell_order.quantity > qty:
                self.add_order(Order(
                    order_type=OrderType.SELL,
                    trader_id=sell_order.trader_id,
                    price=sell_order.price,
                    quantity=sell_order.quantity - qty,
                    timestamp=sell_order.timestamp
                ))

        return trades