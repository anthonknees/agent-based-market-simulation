from __future__ import annotations

import os
import json
import random
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

import numpy as np

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
    jump_tau: float = 0.02
    output_dir: str = "data"
    run_id: str = "001"
    # Trader composition fractions (must sum to 1.0)
    frac_random: float = 0.34
    frac_momentum: float = 0.33
    frac_mean_reversion: float = 0.33
    # Strategy parameters
    random_delta: float = 2.0
    random_qmax: int = 5
    momentum_lookback: int = 10
    momentum_theta: float = 1.0
    momentum_kappa: float = 0.5
    momentum_qmax: int = 4
    meanrev_window: int = 20
    meanrev_theta: float = 1.0
    meanrev_kappa: float = 0.5
    meanrev_qmax: int = 4
    # Legacy compat
    output_csv: str = ""

    def __post_init__(self):
        if not self.output_csv:
            self.output_csv = os.path.join(self.output_dir, f"run_{self.run_id}_timeseries.csv")


class SimulationController:
    def __init__(self, config: SimulationConfig) -> None:
        self.cfg = config
        random.seed(self.cfg.seed)
        np.random.seed(self.cfg.seed)

        self.market = Market(self.cfg.initial_price)
        self.traders = self._create_traders(self.cfg.num_traders)
        self.market.order_book.register_traders(self.traders)

        self.price_history: List[float] = [self.market.current_price]
        self.rows: list[dict] = []

        # Track per-trader order submissions and fills for performance metrics
        self._orders_submitted: Dict[int, int] = {t.id: 0 for t in self.traders}
        self._orders_filled: Dict[int, int] = {t.id: 0 for t in self.traders}
        self._initial_portfolios: Dict[int, dict] = {}
        for t in self.traders:
            self._initial_portfolios[t.id] = {
                "capital": t.capital,
                "inventory": t.inventory,
                "value": t.capital + t.inventory * self.cfg.initial_price,
            }

        # Portfolio value history for drawdown calculation
        self._portfolio_history: Dict[int, List[float]] = {t.id: [] for t in self.traders}

        # Execution timing
        self.execution_time_sec: float = 0.0

    def _create_traders(self, n: int):
        n_random = max(1, int(n * self.cfg.frac_random))
        n_momentum = max(1, int(n * self.cfg.frac_momentum))
        n_meanrev = n - n_random - n_momentum
        if n_meanrev < 1:
            n_meanrev = 1
            n_random = n - n_momentum - n_meanrev

        strategies = (
            [RandomStrategy(delta=self.cfg.random_delta, qmax=self.cfg.random_qmax)] * n_random
            + [MomentumStrategy(lookback=self.cfg.momentum_lookback, theta=self.cfg.momentum_theta,
                                kappa=self.cfg.momentum_kappa, qmax=self.cfg.momentum_qmax)] * n_momentum
            + [MeanReversionStrategy(window=self.cfg.meanrev_window, theta=self.cfg.meanrev_theta,
                                     kappa=self.cfg.meanrev_kappa, qmax=self.cfg.meanrev_qmax)] * n_meanrev
        )

        traders = []
        for i in range(n):
            start_inventory = random.randint(5, 20)
            traders.append(
                Trader(
                    id=i,
                    capital=10_000.0,
                    inventory=start_inventory,
                    strategy=strategies[i % len(strategies)]
                )
            )
        return traders

    def run(self) -> dict:
        start_wall = time.time()

        for t in range(1, self.cfg.max_time + 1):
            # Count orders submitted this step
            for tr in self.traders:
                before_count = len(self.market.order_book._buy) + len(self.market.order_book._sell)
                tr.decide_action(self.market, t, self.price_history)
                after_count = len(self.market.order_book._buy) + len(self.market.order_book._sell)
                if after_count > before_count:
                    self._orders_submitted[tr.id] += 1

            # Match/execute trades and update price
            trades = self.market.order_book.match_orders()
            volume = 0
            last_price = None
            for trade in trades:
                buyer = trade["buyer"]
                seller = trade["seller"]
                price = trade["price"]
                qty = trade["quantity"]
                volume += qty
                last_price = price
                buyer.capital -= qty * price
                buyer.inventory += qty
                seller.capital += qty * price
                seller.inventory -= qty
                # Track fills
                self._orders_filled[buyer.id] = self._orders_filled.get(buyer.id, 0) + 1
                self._orders_filled[seller.id] = self._orders_filled.get(seller.id, 0) + 1

            if last_price is not None:
                self.market.current_price = last_price
            self.price_history.append(self.market.current_price)

            # Record portfolio values for drawdown
            for tr in self.traders:
                pv = tr.capital + tr.inventory * self.market.current_price
                self._portfolio_history[tr.id].append(pv)

            bid, ask = self.market.order_book.best_bid_ask()
            spread = (ask - bid) if (bid is not None and ask is not None) else None

            self.rows.append({
                "time": t,
                "price": self.market.current_price,
                "bid": bid,
                "ask": ask,
                "spread": spread,
                "volume": volume,
                "last_trade_price": last_price,
            })

        self.execution_time_sec = time.time() - start_wall

        # Compute analytics
        logrets = compute_log_returns(self.price_history)
        rv = rolling_volatility(logrets, self.cfg.vol_window)
        jump_rate = float((abs(logrets) > self.cfg.jump_tau).mean()) if len(logrets) > 0 else 0.0
        mean_vol = float(rv.mean()) if len(rv) > 0 else 0.0

        # Per-strategy performance
        strategy_perf = self._compute_strategy_performance()

        # Build run summary
        summary = {
            "run_id": self.cfg.run_id,
            "steps": self.cfg.max_time,
            "num_traders": self.cfg.num_traders,
            "seed": self.cfg.seed,
            "initial_price": self.cfg.initial_price,
            "final_price": round(self.price_history[-1], 4),
            "price_return_pct": round((self.price_history[-1] / self.cfg.initial_price - 1) * 100, 4),
            "jump_rate": round(jump_rate, 6),
            "mean_rolling_vol": round(mean_vol, 6),
            "total_volume": sum(r["volume"] for r in self.rows),
            "mean_spread": round(np.nanmean([r["spread"] for r in self.rows if r["spread"] is not None]), 4) if any(r["spread"] is not None for r in self.rows) else None,
            "execution_time_sec": round(self.execution_time_sec, 3),
            "strategy_performance": strategy_perf,
        }

        # Save outputs
        os.makedirs(self.cfg.output_dir, exist_ok=True)
        write_metrics_csv(self.cfg.output_csv, self.rows)

        config_path = os.path.join(self.cfg.output_dir, f"run_{self.cfg.run_id}_config.json")
        with open(config_path, "w") as f:
            cfg_dict = {k: v for k, v in asdict(self.cfg).items() if k != "output_csv"}
            json.dump(cfg_dict, f, indent=2)

        summary_path = os.path.join(self.cfg.output_dir, f"run_{self.cfg.run_id}_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"=== Run {self.cfg.run_id} Summary ===")
        print(f"  Steps: {self.cfg.max_time}  |  Traders: {self.cfg.num_traders}  |  Seed: {self.cfg.seed}")
        print(f"  Final Price: {self.price_history[-1]:.2f}  |  Return: {summary['price_return_pct']:.2f}%")
        print(f"  Jump Rate: {jump_rate:.4f}  |  Mean Vol: {mean_vol:.6f}")
        print(f"  Total Volume: {summary['total_volume']}  |  Mean Spread: {summary['mean_spread']}")
        print(f"  Execution Time: {self.execution_time_sec:.3f}s")
        for sp in strategy_perf:
            print(f"  [{sp['strategy']}] Return: {sp['mean_total_return_pct']:.2f}%  Sharpe: {sp['mean_sharpe']:.4f}  MaxDD: {sp['mean_max_drawdown_pct']:.2f}%  FillRate: {sp['mean_fill_rate']:.2f}%")
        print(f"  Saved: {self.cfg.output_csv}")

        return summary

    def _compute_strategy_performance(self) -> list[dict]:
        """Compute per-strategy aggregated performance metrics."""
        strategy_groups: Dict[str, list] = {}
        for tr in self.traders:
            sname = tr.strategy.name
            if sname not in strategy_groups:
                strategy_groups[sname] = []
            strategy_groups[sname].append(tr)

        results = []
        for sname, traders in strategy_groups.items():
            total_returns = []
            sharpe_ratios = []
            max_drawdowns = []
            fill_rates = []

            for tr in traders:
                init = self._initial_portfolios[tr.id]
                final_value = tr.capital + tr.inventory * self.market.current_price
                total_ret = (final_value - init["value"]) / init["value"]
                total_returns.append(total_ret * 100)

                # Sharpe ratio from portfolio value time series
                pv_hist = self._portfolio_history[tr.id]
                if len(pv_hist) > 1:
                    pv_returns = []
                    for i in range(1, len(pv_hist)):
                        pv_returns.append((pv_hist[i] - pv_hist[i - 1]) / pv_hist[i - 1])
                    pv_ret_arr = np.array(pv_returns)
                    mean_r = pv_ret_arr.mean()
                    std_r = pv_ret_arr.std(ddof=1) if len(pv_ret_arr) > 1 else 1e-9
                    sharpe = mean_r / std_r if std_r > 1e-12 else 0.0
                else:
                    sharpe = 0.0
                sharpe_ratios.append(sharpe)

                # Max drawdown
                if pv_hist:
                    peak = pv_hist[0]
                    max_dd = 0.0
                    for v in pv_hist:
                        if v > peak:
                            peak = v
                        dd = (peak - v) / peak if peak > 0 else 0.0
                        if dd > max_dd:
                            max_dd = dd
                    max_drawdowns.append(max_dd * 100)
                else:
                    max_drawdowns.append(0.0)

                # Fill rate
                submitted = self._orders_submitted.get(tr.id, 0)
                filled = self._orders_filled.get(tr.id, 0)
                fr = (filled / submitted * 100) if submitted > 0 else 0.0
                fill_rates.append(fr)

            results.append({
                "strategy": sname,
                "num_traders": len(traders),
                "mean_total_return_pct": round(float(np.mean(total_returns)), 4),
                "std_total_return_pct": round(float(np.std(total_returns)), 4),
                "mean_sharpe": round(float(np.mean(sharpe_ratios)), 6),
                "mean_max_drawdown_pct": round(float(np.mean(max_drawdowns)), 4),
                "mean_fill_rate": round(float(np.mean(fill_rates)), 4),
            })

        return results
