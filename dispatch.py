"""
Economic dispatch LP for a single day (24 hours).

Decision variables:
    p[g, t]  -- output of generator g in hour t (MW)
    s[g, t]  -- slack for curtailment of renewables (MW)

Minimize:
    sum over g,t of cost[g] * p[g,t]

Subject to:
    (1) balance:       sum_g p[g,t] == demand[t]          for all t
    (2) capacity:      p_min[g] <= p[g,t] <= p_max[g]     for all g, t
    (3) ramp up:       p[g,t] - p[g,t-1] <= ramp[g]       for all g, t>0
    (4) ramp down:     p[g,t-1] - p[g,t] <= ramp[g]       for all g, t>0
    (5) must-run:      p[g,t] >= p_min[g]  if must_run[g]  (already covered by (2))
    (6) reserve:       sum_g p[g,t] >= demand[t] * (1 + reserve_margin)
    (7) zone flow:     zone_net_export[z,t] <= flow_limit[z]
    (8) curtailment:   p[g,t] + s[g,t] == p_max[g]  for renewables (optional formulation)
"""

import pulp
import pandas as pd
import numpy as np


RESERVE_MARGIN = 0.10   # 10% spinning reserve above peak
CURTAIL_PENALTY = 5     # $/MWh penalty for curtailing zero-cost renewables

# rough inter-zone transfer limits (MW) -- placeholder, refine from IESO docs
ZONE_FLOW_LIMITS = {
    "Toronto":   2500,
    "East":      1200,
    "West":      1800,
    "Northwest": 800,
    "Niagara":   1500,
    "Southwest": 900,
}


def build_model(fleet, demand_series):
    """
    fleet: DataFrame from generators.get_fleet()
    demand_series: array-like of length 24 (MW)
    returns: (prob, p_vars, s_vars)
    """

    T = range(24)
    G = fleet.index.tolist()
    RENEWABLES = fleet[fleet["fuel"].isin(["wind", "solar"])].index.tolist()

    prob = pulp.LpProblem("ontario_dispatch", pulp.LpMinimize)

    # --- decision variables ---
    p = pulp.LpVariable.dicts("p", (G, T), lowBound=0)
    s = pulp.LpVariable.dicts("s", (RENEWABLES, T), lowBound=0)  # curtailment slack

    # --- objective ---
    gen_cost = pulp.lpSum(
        fleet.loc[g, "cost"] * p[g][t]
        for g in G for t in T
    )
    curtail_cost = pulp.lpSum(
        CURTAIL_PENALTY * s[g][t]
        for g in RENEWABLES for t in T
    )
    prob += gen_cost + curtail_cost

    for t in T:
        demand_t = float(demand_series[t])

        # (1) balance
        prob += pulp.lpSum(p[g][t] for g in G) == demand_t, f"balance_{t}"

        # (6) spinning reserve
        prob += pulp.lpSum(p[g][t] for g in G) >= demand_t * (1 + RESERVE_MARGIN), f"reserve_{t}"

        for g in G:
            row = fleet.loc[g]

            # (2) capacity bounds
            prob += p[g][t] >= row["p_min"], f"pmin_{g}_{t}"
            prob += p[g][t] <= row["p_max"], f"pmax_{g}_{t}"

            # (3)/(4) ramp limits
            if t > 0:
                prob += p[g][t] - p[g][t-1] <= row["ramp_mw_hr"], f"ramp_up_{g}_{t}"
                prob += p[g][t-1] - p[g][t] <= row["ramp_mw_hr"], f"ramp_dn_{g}_{t}"

        # (8) curtailment accounting for renewables
        for g in RENEWABLES:
            prob += p[g][t] + s[g][t] == fleet.loc[g, "p_max"], f"curtail_{g}_{t}"

    # (7) zone flow limits (net injection per zone per hour)
    zones = fleet["zone"].unique()
    for z in zones:
        z_gens = fleet[fleet["zone"] == z].index.tolist()
        limit = ZONE_FLOW_LIMITS.get(z, 1000)
        for t in T:
            prob += pulp.lpSum(p[g][t] for g in z_gens) <= limit, f"flow_{z}_{t}"

    return prob, p, s


def solve(prob):
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    status = pulp.LpStatus[prob.status]
    print(f"status: {status}  |  total cost: ${pulp.value(prob.objective):,.0f}")
    return status


def extract_results(p_vars, fleet, T=range(24)):
    records = []
    for g in fleet.index:
        for t in T:
            records.append({
                "generator": fleet.loc[g, "name"],
                "fuel":      fleet.loc[g, "fuel"],
                "zone":      fleet.loc[g, "zone"],
                "hour":      t,
                "output_mw": pulp.value(p_vars[g][t]) or 0.0,
                "cost":      fleet.loc[g, "cost"],
            })
    return pd.DataFrame(records)


if __name__ == "__main__":
    from generators import get_fleet

    fleet = get_fleet()

    # placeholder flat demand -- replace with real IESO data
    np.random.seed(42)
    demand = 14000 + 2000 * np.sin(np.linspace(0, np.pi, 24)) + np.random.normal(0, 200, 24)

    prob, p, s = build_model(fleet, demand)
    solve(prob)

    results = extract_results(p, fleet)
    results.to_csv("data/processed/dispatch_results.csv", index=False)
    print(results.groupby(["hour", "fuel"])["output_mw"].sum().unstack().to_string())
