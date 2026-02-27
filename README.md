# Agent-Based Financial Market Simulation

## Project Overview

This project implements an agent-based financial market simulation in which autonomous trader agents interact through a centralized limit order book. The objective is to study how competing trading strategies influence price dynamics, liquidity, and market stability.

The system models a simplified electronic exchange where traders submit buy and sell orders that are matched using price-time priority**, producing emergent market behavior over time.

This repository currently contains the Milestone 2 initial implementation of the simulation.

---

Project Status (Milestone 2)

### Implemented Features

- Discrete-time agent-based market simulation
- Centralized limit order book
- Heap-based price-time priority matching algorithm
- Autonomous trader agents with portfolios
- Multiple trading strategies:
  - Random Strategy
  - Momentum Strategy
  - Mean-Reversion Strategy
- Stochastic order submission and sizing
- Trade execution and settlement
- Market price updates from executed trades
- Automated metric collection
- CSV output of simulation data

---

### Planned Features (Future Milestones)

- Order cancellation mechanisms
- Market-maker liquidity agents
- Multi-run experimental framework
- Strategy performance evaluation:
  - Sharpe ratio
  - drawdown analysis
  - fill-rate comparison
- Visualization and statistical analysis tools
- Emergent behavior experimentation

---

## Changes From Original Proposal

The original Milestone 1 proposal described a conceptual agent-based market model.  
During implementation, several practical adjustments were made:

- A discrete-time simulation loop was implemented instead of a fully event-driven engine to simplify development.
- Adaptive or learning agents were postponed to later milestones.
- Transaction costs and order cancellation were deferred to focus on establishing core market mechanics first.

These decisions ensured a stable executable foundation before expanding

---

## Installation Instructions

### 1. Clone Repository
```bash
git clone https://github.com/anthonknees/agent-based-market-simulation.git
cd agent-based-market-simulation

---

## Create Virtual Environment

python -m venv .venv
source .venv/bin/activate

## Install Dependencies

pip install -r requirements.txt

### If dependencies fail to install:

pip install --upgrade pip
pip install -r requirements.txt

## Usage

python src/main.py

Simulation Configuration

## Simulation behavior is controlled through configuration parameters including:

- number of simulation steps

- trader participation rate

- stochastic order behavior

- strategy-specific parameters

- random seed initialization

These parameters allow experimentation with different market environments.


## Expected Output

Simulation results are automatically saved to
  data/metrics.csv
