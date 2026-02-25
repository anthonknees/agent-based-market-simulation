from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Order:
    order_type: OrderType
    trader_id: int
    price: float
    quantity: int
    timestamp: int