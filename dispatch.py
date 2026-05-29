import cvxpy as cp
import numpy as np
import pandas as pd


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


def con_reserve(fleet, p, demand, T, margin=0.10):
    constraints = []
    for t in T:
        total = sum(p[g, t] for g in fleet.index)
        constraints.append(total >= demand[t] * (1 + margin))
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
                # force u[g, t] == 1
                u[g, t] == 1
                ...
        elif init < 0:
            hours_locked_off = max(0, min_dn - abs(init))
            for t in range(hours_locked_off):
                # force u[g, t] == 0
                u[g, t] == 0
                ...

        # --- general min up: if unit starts up at t, must stay on for min_up hours ---
        for t in T:
            if t == 0:
                continue  # handled by initial lock-in
            # hint: use v[g, t] here -- but we haven't built v yet
            # for now just leave as ... and we'll wire it in after con_startup_indicator
            ...

        # --- general min dn: same idea for shutdowns ---
        for t in T:
            ...

    return constraints