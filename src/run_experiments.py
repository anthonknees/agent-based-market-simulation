#!/usr/bin/env python3
"""
Milestone 3 Experiment Runner
Executes 12 distinct simulation runs varying num_traders, frac_momentum, and max_time.
Collects comprehensive data for each run and produces a consolidated results CSV.
"""
from __future__ import annotations

import json
import os
import csv
import time
from dataclasses import asdict

from simulation_controller import SimulationController, SimulationConfig

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "m3_runs")


def build_experiments() -> list[SimulationConfig]:
    """Define 12 experiment configurations varying 3+ parameters."""
    experiments = []

    # --- Run 001: Baseline (all defaults) ---
    experiments.append(SimulationConfig(
        run_id="001", max_time=500, seed=42, num_traders=30,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 002: More traders (60) ---
    experiments.append(SimulationConfig(
        run_id="002", max_time=500, seed=42, num_traders=60,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 003: Fewer traders (10) ---
    experiments.append(SimulationConfig(
        run_id="003", max_time=500, seed=42, num_traders=10,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 004: High momentum composition (60% momentum) ---
    experiments.append(SimulationConfig(
        run_id="004", max_time=500, seed=42, num_traders=30,
        frac_random=0.20, frac_momentum=0.60, frac_mean_reversion=0.20,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 005: High mean-reversion composition (60% MR) ---
    experiments.append(SimulationConfig(
        run_id="005", max_time=500, seed=42, num_traders=30,
        frac_random=0.20, frac_momentum=0.20, frac_mean_reversion=0.60,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 006: High random composition (60% random) ---
    experiments.append(SimulationConfig(
        run_id="006", max_time=500, seed=42, num_traders=30,
        frac_random=0.60, frac_momentum=0.20, frac_mean_reversion=0.20,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 007: Longer simulation (1000 steps) ---
    experiments.append(SimulationConfig(
        run_id="007", max_time=1000, seed=42, num_traders=30,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 008: Short simulation (200 steps) ---
    experiments.append(SimulationConfig(
        run_id="008", max_time=200, seed=42, num_traders=30,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 009: Large market stress (100 traders, 1000 steps) ---
    experiments.append(SimulationConfig(
        run_id="009", max_time=1000, seed=42, num_traders=100,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 010: Different seed for reproducibility check ---
    experiments.append(SimulationConfig(
        run_id="010", max_time=500, seed=123, num_traders=30,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 011: Another seed + high traders ---
    experiments.append(SimulationConfig(
        run_id="011", max_time=500, seed=999, num_traders=50,
        frac_random=0.34, frac_momentum=0.33, frac_mean_reversion=0.33,
        output_dir=OUTPUT_DIR,
    ))

    # --- Run 012: Momentum-dominated + long run ---
    experiments.append(SimulationConfig(
        run_id="012", max_time=1000, seed=77, num_traders=40,
        frac_random=0.15, frac_momentum=0.70, frac_mean_reversion=0.15,
        output_dir=OUTPUT_DIR,
    ))

    return experiments


def run_all() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    experiments = build_experiments()
    all_summaries = []

    print(f"Running {len(experiments)} experiments...\n")

    for cfg in experiments:
        print(f"--- Starting Run {cfg.run_id} ---")
        sim = SimulationController(cfg)
        summary = sim.run()
        all_summaries.append(summary)
        print()

    # Write consolidated results CSV
    results_csv_path = os.path.join(OUTPUT_DIR, "all_runs_results.csv")
    fieldnames = [
        "run_id", "steps", "num_traders", "seed", "initial_price",
        "final_price", "price_return_pct", "jump_rate", "mean_rolling_vol",
        "total_volume", "mean_spread", "execution_time_sec",
        # Strategy performance columns (flattened)
        "random_return_pct", "random_sharpe", "random_maxdd_pct", "random_fill_rate",
        "momentum_return_pct", "momentum_sharpe", "momentum_maxdd_pct", "momentum_fill_rate",
        "meanrev_return_pct", "meanrev_sharpe", "meanrev_maxdd_pct", "meanrev_fill_rate",
    ]

    with open(results_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in all_summaries:
            row = {k: s.get(k) for k in fieldnames[:12]}
            # Flatten strategy performance
            for sp in s.get("strategy_performance", []):
                sname = sp["strategy"].lower()
                if "random" in sname:
                    prefix = "random"
                elif "momentum" in sname:
                    prefix = "momentum"
                else:
                    prefix = "meanrev"
                row[f"{prefix}_return_pct"] = sp["mean_total_return_pct"]
                row[f"{prefix}_sharpe"] = sp["mean_sharpe"]
                row[f"{prefix}_maxdd_pct"] = sp["mean_max_drawdown_pct"]
                row[f"{prefix}_fill_rate"] = sp["mean_fill_rate"]
            writer.writerow(row)

    print(f"\nConsolidated results saved to: {results_csv_path}")

    # Also save a master JSON index
    index_path = os.path.join(OUTPUT_DIR, "run_index.json")
    with open(index_path, "w") as f:
        json.dump(all_summaries, f, indent=2, default=str)
    print(f"Run index saved to: {index_path}")


if __name__ == "__main__":
    run_all()
