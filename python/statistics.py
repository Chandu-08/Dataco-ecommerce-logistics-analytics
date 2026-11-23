"""Order-level Wilson intervals and descriptive comparisons; no causal claims."""
from pathlib import Path
from math import sqrt
import pandas as pd

root = Path(__file__).resolve().parents[1]
orders = pd.read_csv(root / "data/processed/fact_orders.csv")
orders = orders[orders.logistics_eligible]


def wilson(success, n, z=1.96):
    p = success / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (center - half, center + half)


rows = []
for mode, g in orders.groupby("shipping_mode"):
    n, k = len(g), int(g.late.sum())
    low, high = wilson(k, n)
    rows.append({"shipping_mode": mode, "orders": n, "late_orders": k,
                 "late_rate": k / n, "wilson_low": low, "wilson_high": high})
out = pd.DataFrame(rows)
out.to_csv(root / "data/processed/shipping_mode_intervals.csv", index=False)
print(out.to_string(index=False))
