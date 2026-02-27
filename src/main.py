from __future__ import annotations

from simulation_controller import SimulationController, SimulationConfig


def main() -> None:
    cfg = SimulationConfig(
        max_time=500,
        seed=42,
        initial_price=100.0,
        num_traders=30,
        vol_window=50,
        jump_tau=0.02,
        output_csv="data/metrics.csv"
    )
    sim = SimulationController(cfg)
    sim.run()


if __name__ == "__main__":
    main()