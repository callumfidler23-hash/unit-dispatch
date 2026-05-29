from generators import get_fleet_5unit, DEMAND_5
from dispatch import solve, extract_results

def main():
    fleet = get_fleet_5unit()
    prob, p, u, v = solve(fleet, DEMAND_5)

    if prob.status == "optimal":
        results = extract_results(prob, p, u, v, fleet, DEMAND_5)
        results.to_csv("data/processed/dispatch_results.csv", index=False)
        print(results)
    else:
        print(f"solver did not find optimal solution -- status: {prob.status}")

if __name__ == "__main__":
    main()