# Unit Commitment Optimizer

A mixed-integer linear program (MILP) for the thermal unit commitment problem, implemented in Python following the formulation in Kazarlis, Bakirtzis & Petridis (1996).

## Problem

The unit commitment problem asks: given a set of thermal generators and a 24-hour demand forecast, which generators should be on or off each hour, and at what output level, to minimize total production cost?

It is a MILP because each generator has both a continuous decision (output in MW) and a binary decision (on or off). The binary variables interact with the continuous ones through capacity and minimum stable generation constraints, making it significantly harder than a pure LP.

## Formulation

**Objective:** Minimize total fuel cost + startup costs over 24 hours

**Decision variables:**
- `p[g, t]` — output of generator g in hour t (MW, continuous)
- `u[g, t]` — commitment status of generator g in hour t (binary)
- `v[g, t]` — startup indicator, 1 when generator transitions off→on (binary)

**Constraints:**
- Hourly supply/demand balance
- Generator capacity bounds conditional on commitment (`p_min * u <= p <= p_max * u`)
- Ramp rate limits between consecutive hours
- Spinning reserve requirement (10% above demand)
- Minimum up time — once started, must run for at least N hours
- Minimum down time — once shut down, must stay off for at least M hours
- Initial condition lock-in based on prior operating status
- Startup indicator linking v to transitions in u

## Validation

Benchmarked against the 10-unit test case from Kazarlis et al. (1996), Table II.

| | Cost ($) |
|---|---|
| This model | 557,200 |
| Paper (DP/LR optimal) | 565,825 |

The model comes in slightly below the paper's figure due to the linear cost approximation (the paper uses a quadratic fuel cost function `fc = a + b·P + c·P²`; this model uses the linear terms only). Commitment decisions match well.

## Stack

- `cvxpy` — problem formulation
- `pyscipopt` / SCIP — MILP solver
- `pandas` — data handling

## Usage

```bash
pip install -r requirements.txt
python run.py
```

## Extensions

The natural next steps from this formulation are:

- **Piecewise linear cost** — approximating the quadratic fuel cost curve with linear segments, recovering the full cost accuracy without the MIQP complexity
- **Cold/hot startup costs** — currently all startups use the hot start cost; the paper distinguishes based on how long the unit has been down
- **Ontario fleet** — replacing the benchmark generators with real IESO data and adding transmission zone constraints

## Reference

S.A. Kazarlis, A.G. Bakirtzis, V. Petridis, "A Genetic Algorithm Solution to the Unit Commitment Problem," *IEEE Transactions on Power Systems*, vol. 11, no. 1, February 1996.