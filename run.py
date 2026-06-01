from generators import get_fleet_10unit, DEMAND_10
from dispatch import solve, extract_results

def main():
    fleet = get_fleet_10unit()
    prob, p, u, v = solve(fleet, DEMAND_10)

    if prob.status == "optimal":
        results = extract_results(prob, p, u, v, fleet, DEMAND_10)
        results.to_csv("data/processed/dispatch_results.csv", index=False)
        print(results)
    else:
        print(f"solver did not find optimal solution -- status: {prob.status}")

if __name__ == "__main__":
    main()