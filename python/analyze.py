"""Create aggregated analyses and figures from locally generated facts."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed"
FIG = ROOT / "dashboards"
FIG.mkdir(exist_ok=True)
i = pd.read_csv(DATA / "fact_order_items.csv", parse_dates=["order_date"])
o = pd.read_csv(DATA / "fact_orders.csv", parse_dates=["order_date"])
r = pd.read_csv(DATA / "customer_rfm.csv")
f = i[i.financial_eligible].copy()
v = o[o.financial_eligible].copy()
l = o[o.logistics_eligible].copy()
f["month"] = f.order_date.dt.to_period("M").astype(str)


def write(name, frame):
    frame.to_csv(DATA / (name + ".csv"), index=False)
    return frame


def by(group):
    z = f.groupby(group, dropna=False).agg(items=("order_item_id", "size"), sales=("net_sales", "sum"), profit=("profit", "sum"), discount=("discount", "sum")).reset_index()
    z["margin_pct"] = 100 * z.profit / z.sales.where(z.sales.ne(0))
    return write("financial_by_" + group, z.sort_values("sales", ascending=False))


category = by("category")
market = by("market")
by("month")
by("product")
by("region")
f["discount_band"] = pd.cut(f.discount / f.gross_sales.where(f.gross_sales.gt(0)), bins=[-0.001, .05, .10, .20, .30, 1], labels=["0–5%", "5–10%", "10–20%", "20–30%", "30%+"])
write("discount_analysis", f.groupby("discount_band", observed=False).agg(items=("order_item_id", "size"), sales=("net_sales", "sum"), profit=("profit", "sum")).reset_index())
segments = write("segment_summary", r.groupby("segment").agg(customers=("customer_id", "size"), sales=("monetary", "sum"), mean_orders=("frequency", "mean"), mean_recency=("recency_days", "mean")).reset_index())
segments["sales_share_pct"] = 100 * segments.sales / segments.sales.sum()
write("segment_summary", segments)
for g in ("shipping_mode", "market", "region"):
    z = l.groupby(g).agg(orders=("order_id", "size"), late_orders=("late", "sum"), sales=("net_sales", "sum"), avg_actual_days=("actual_days", "mean"), avg_scheduled_days=("scheduled_days", "mean"), avg_delay_days=("delay_days", "mean")).reset_index()
    z["late_pct"] = 100 * z.late_orders / z.orders
    exposure = l[l.late].groupby(g).net_sales.sum().rename("late_sales_exposure")
    z = z.merge(exposure, on=g, how="left").fillna({"late_sales_exposure": 0})
    write("logistics_by_" + g, z.sort_values("late_orders", ascending=False))
# Category membership is item grain; count each order once per category.
cat_orders = f[["order_id", "category"]].drop_duplicates().merge(l[["order_id", "late"]], on="order_id")
write("logistics_by_category", cat_orders.groupby("category").agg(orders_with_category=("order_id", "nunique"), late_orders_with_category=("late", "sum")).reset_index())
high = set(r.loc[r.segment.eq("High-value repeat"), "customer_id"])
l["high_value_repeat"] = l.customer_id.isin(high)
write("customer_delivery_cross", l.groupby("high_value_repeat").agg(orders=("order_id", "size"), late_orders=("late", "sum"), sales=("net_sales", "sum")).reset_index())

plt.style.use("seaborn-v0_8-whitegrid")
fig, ax = plt.subplots(figsize=(9, 4))
monthly = f.groupby("month").net_sales.sum()
monthly.plot(ax=ax, color="#176b83")
ax.set(title="Completed-order net sales by month", ylabel="Recorded net sales", xlabel="Order month")
fig.tight_layout(); fig.savefig(FIG / "monthly_sales.png", dpi=160); plt.close(fig)
fig, ax = plt.subplots(figsize=(8, 4))
seg = segments.set_index("segment").sort_values("sales").sales
seg.plot.barh(ax=ax, color="#458f72")
ax.set(title="Recorded net sales by customer segment", xlabel="Recorded net sales")
fig.tight_layout(); fig.savefig(FIG / "segments.png", dpi=160); plt.close(fig)
fig, ax = plt.subplots(figsize=(8, 4))
mode = pd.read_csv(DATA / "logistics_by_shipping_mode.csv").set_index("shipping_mode").sort_values("late_pct")
mode.late_pct.plot.barh(ax=ax, color="#d97757")
ax.set(title="Late orders by shipping mode (completed only)", xlabel="Late orders (%)", xlim=(0, 105))
fig.tight_layout(); fig.savefig(FIG / "shipping_mode.png", dpi=160); plt.close(fig)
if (DATA / "product_interest.csv").exists():
    interest = pd.read_csv(DATA / "product_interest.csv")
    fig, ax = plt.subplots(figsize=(9, 5))
    top = interest.nlargest(10, "page_events").sort_values("page_events")
    top.set_index("product").page_events.plot.barh(ax=ax, color="#7868aa")
    ax.set(title="Most viewed products in access logs", xlabel="Page events (not unique visitors)")
    fig.tight_layout(); fig.savefig(FIG / "product_interest.png", dpi=160); plt.close(fig)
print(json.dumps({"category_count": len(category), "market_count": len(market), "segment_count": len(segments)}, indent=2))
