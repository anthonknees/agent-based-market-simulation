from __future__ import annotations
from order_book import OrderBook


class Market:
    def __init__(self, initial_price: float) -> None:
        self.current_price = float(initial_price)
        self.order_book = OrderBook()

    def execute_trades(self) -> dict:
        """
        Matches orders, settles cash/inventory, and updates price.
        Price update rule: last trade price in this step; if none, price unchanged.
        Returns a dict summary (volume, last_trade_price).
        """
        trades = self.order_book.match_orders()
        volume = 0
        last_price = None

        for tr in trades:
            buyer = tr["buyer"]
            seller = tr["seller"]
            price = tr["price"]
            qty = tr["quantity"]

            volume += qty
            last_price = price

            buyer.capital -= qty * price
            buyer.inventory += qty

            seller.capital += qty * price
            seller.inventory -= qty

        if last_price is not None:
            self.current_price = last_price

        return {"volume": volume, "last_trade_price": last_price}