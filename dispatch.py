import cvxpy as cp
import numpy as np
import pandas as pd

print("dispatch.py loaded")
def build_variables(fleet, T):
    G = fleet.index.tolist()

    p = {(g, t): cp.Variable(nonneg=True) for g in G for t in T}
    u = {(g, t): cp.Variable(boolean=True) for g in G for t in T}
    v = {(g, t): cp.Variable(boolean=True) for g in G for t in T}

    return p, u, v


def initial_state(row):
    was_on = 1 if row["initial_status"] > 0 else 0
    return was_on


def con_capacity(fleet, p, u, T):
    constraints = []
    for g in fleet.index:
        p_min = fleet.loc[g, "p_min"]
        p_max = fleet.loc[g, "p_max"]
        for t in T:
            constraints.append(p[g, t] >= p_min * u[g, t])
            constraints.append(p[g, t] <= p_max * u[g, t])
    return constraints


def con_balance(fleet, p, demand, T):
    constraints = []
    for t in T:
        total = sum(p[g, t] for g in fleet.index)
        constraints.append(total == demand[t])
    return constraints


def con_reserve(fleet, p, u, demand, T, margin=0.10):
    constraints = []
    for t in T:
        available = sum(fleet.loc[g, "p_max"] * u[g, t] for g in fleet.index)
        constraints.append(available >= demand[t] * (1 + margin))
    return constraints

def con_ramp(fleet, p, u, T):
    constraints = []
    for g in fleet.index:
        ramp = fleet.loc[g, "ramp"]
        p0 = fleet.loc[g, "p_min"] if initial_state(fleet.loc[g]) else 0
        for t in T:
            if t == 0:
                constraints.append(p[g, t] - p0 <= ramp)
                constraints.append(p0 - p[g, t] <= ramp)
            else:
                # your turn -- same idea but p[g, t-1] instead of p0
                constraints.append(p[g, t] - p[g, t-1] <= ramp)
                constraints.append(p[g, t-1] - p[g, t] <= ramp)
    return constraints

def con_min_up_dn(fleet, u, T):
    constraints = []
    for g in fleet.index:
        min_up = fleet.loc[g, "min_up"]
        min_dn = fleet.loc[g, "min_dn"]
        init   = fleet.loc[g, "initial_status"]

        # --- initial lock-in ---
        if init > 0:
            hours_locked_on = max(0, min_up - init)
            for t in range(hours_locked_on):
                constraints.append(u[g, t] == 1)
        elif init < 0:
            hours_locked_off = max(0, min_dn - abs(init))
            for t in range(hours_locked_off):
                constraints.append(u[g, t] == 0)

        # --- general min up ---
        for t in T:
            if t == 0:
                continue
            for t2 in range(t, min(t + min_up, len(T))):
                constraints.append(u[g, t2] >= u[g, t] - u[g, t-1])

        # --- general min dn ---
        for t in T:
            if t == 0:
                continue
            for t2 in range(t, min(t + min_dn, len(T))):
                constraints.append(u[g, t2] <= 1 - (u[g, t-1] - u[g, t]))

    return constraints

def con_startup_indicator(fleet, v, u, T):
    constraints = []
    for g in fleet.index:
        u0 = initial_state(fleet.loc[g])
        for t in T:
            if t == 0:
                constraints.append(v[g, t] >= u[g, t] - u0)
            else:
                constraints.append(v[g, t] >= u[g, t] - u[g, t-1])
    return constraints

def build_objective(fleet, p, u, v, T):
    fuel_cost = sum(
        fleet.loc[g, "a"] * u[g, t] + fleet.loc[g, "b"] * p[g, t]
        for g in fleet.index for t in T
    )
    startup_cost = sum(
        fleet.loc[g, "hot_start_cost"] * v[g, t]
        for g in fleet.index for t in T
    )
    return fuel_cost + startup_cost

def build_constraints(fleet, p, u, v, demand, T):
    constraints = []
    constraints += con_capacity(fleet, p, u, T)
    constraints += con_balance(fleet, p, demand, T)
    constraints += con_reserve(fleet, p, u, demand, T)
    constraints += con_ramp(fleet, p, u, T)
    constraints += con_min_up_dn(fleet, u, T)
    constraints += con_startup_indicator(fleet, v, u, T)
    return constraints


def solve(fleet, demand):
    T = range(24)
    p, u, v = build_variables(fleet, T)
    print(f"demand length: {len(demand)}")
    print(f"T: {list(T)}")
    print(f"fleet index: {fleet.index.tolist()}")
    print(f"sample p key: {list(p.keys())[:3]}")
    constraints = build_constraints(fleet, p, u, v, demand, T)
    prob = cp.Problem(cp.Minimize(build_objective(fleet, p, u, v, T)), constraints)
    prob.solve(solver=cp.SCIP, verbose=True, scip_params={"numerics/feastol": 1e-6})
    print(f"status: {prob.status}")
    return prob, p, u, v

def extract_results(prob, p, u, v, fleet, demand):
    results = []
    for g in fleet.index:
        for t in range(24):
            results.append({
                "unit": g,
                "hour": t,
                "p": p[g, t].value,
                "u": u[g, t].value,
                "v": v[g, t].value,
            })
    return pd.DataFrame(results)