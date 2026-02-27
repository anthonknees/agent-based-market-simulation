from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import List

from market import Market
from trader import Trader
from metrics import compute_log_returns, rolling_volatility, write_metrics_csv

from strategies.random_strategy import RandomStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy


@dataclass
class SimulationConfig:
    max_time: int = 500
    seed: int = 42
    initial_price: float = 100.0
    num_traders: int = 30
    vol_window: int = 50
    jump_tau: float = 0.02  # jump threshold on log returns
    output_csv: str = "data/metrics.csv"


class SimulationController:
    def __init__(self, config: SimulationConfig) -> None:
        self.cfg = config
        random.seed(self.cfg.seed)

        self.market = Market(self.cfg.initial_price)
        self.traders = self._create_traders(self.cfg.num_traders)
        self.market.order_book.register_traders(self.traders)

        self.price_history: List[float] = [self.market.current_price]
        self.rows: list[dict] = []

    def _create_traders(self, n: int):
        import random
        from trader import Trader
        from strategies.random_strategy import RandomStrategy
        from strategies.momentum_strategy import MomentumStrategy
        from strategies.mean_reversion_strategy import MeanReversionStrategy

        # Build a strategy pool: ~1/3 each
        strategies = (
            [RandomStrategy(delta=2.0, qmax=5)] * max(1, n // 3)
            + [MomentumStrategy(lookback=10, theta=1.0, kappa=0.5, qmax=4)] * max(1, n // 3)
            + [MeanReversionStrategy(window=20, theta=1.0, kappa=0.5, qmax=4)] * max(1, n - 2 * max(1, n // 3))
        )

        traders = []
        for i in range(n):
            start_inventory = random.randint(5, 20)  # gives sell liquidity
            traders.append(
                Trader(
                    id=i,
                    capital=10_000.0,
                    inventory=start_inventory,
                    strategy=strategies[i % len(strategies)]  # NOT "..."
                )
            )
        return traders

    def run(self) -> None:
        for t in range(1, self.cfg.max_time + 1):
            # each step: traders act
            for tr in self.traders:
                tr.decide_action(self.market, t, self.price_history)

            # match/execute trades and update price
            summary = self.market.execute_trades()
            self.price_history.append(self.market.current_price)

            bid, ask = self.market.order_book.best_bid_ask()
            spread = (ask - bid) if (bid is not None and ask is not None) else None

            self.rows.append({
                "time": t,
                "price": self.market.current_price,
                "bid": bid,
                "ask": ask,
                "spread": spread,
                "volume": summary["volume"],
                "last_trade_price": summary["last_trade_price"],
            })

        # compute vol + jumps after run (baseline)
        logrets = compute_log_returns(self.price_history)
        rv = rolling_volatility(logrets, self.cfg.vol_window)
        jump_rate = float((abs(logrets) > self.cfg.jump_tau).mean()) if len(logrets) > 0 else 0.0

        print("=== Run Summary ===")
        print(f"Steps: {self.cfg.max_time}")
        print(f"Final Price: {self.price_history[-1]:.2f}")
        print(f"Jump Rate (|r_t|>{self.cfg.jump_tau}): {jump_rate:.4f}")
        if len(rv) > 0:
            print(f"Mean Rolling Vol (W={self.cfg.vol_window}): {rv.mean():.6f}")

        # write csv
        os.makedirs(os.path.dirname(self.cfg.output_csv), exist_ok=True)
        write_metrics_csv(self.cfg.output_csv, self.rows)
        print(f"Saved metrics to: {self.cfg.output_csv}")