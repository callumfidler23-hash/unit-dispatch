# Ontario Economic Dispatch

A linear programming model for day-ahead electricity dispatch in Ontario, loosely following the IESO economic dispatch methodology.

## What it does

Given hourly load forecasts and a set of generation assets, the LP minimizes total dispatch cost subject to:

- Hourly supply/demand balance
- Generator capacity bounds (min/max MW)
- Ramp rate limits (up and down)
- Spinning reserve requirement (10% above load)
- Zone-level transmission flow limits
- Must-run constraints for nuclear baseload
- Renewable curtailment with penalty

## Data

Demand and price data from [IESO Open Data](https://www.ieso.ca/Power-Data). Generator registry also from IESO. Run `fetch_data.py` before dispatching.

## Usage

```bash
pip install pulp pandas geopandas matplotlib requests

python fetch_data.py          # download IESO demand/price data
python run.py --date 2024-07-15
```

Outputs saved to `outputs/`:
- `dispatch_stack.png` — hourly generation stack by fuel type
- `zone_map.png` — choropleth of generation by planning zone
- `generator_map.png` — geographic scatter of dispatched generators

## Notes

Professional dispatch modeling (PLEXOS, Aurora, PROMOD) wraps a similar LP formulation with unit commitment (MIP), stochastic load scenarios, and N-1 contingency analysis. This project implements the LP core without the binary commitment variables.
