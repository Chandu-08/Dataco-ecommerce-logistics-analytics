"""Reproducible DataCo pipeline. Run: python python/build.py --source data/raw/DataCoSupplyChainDataset.csv"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
FINISHED = {"COMPLETE", "CLOSED"}  # observed completed states; not proof of cash collection
FIELDS = {
    "Order Item Id": "order_item_id", "Order Id": "order_id",
    "Order Customer Id": "customer_id", "Customer Id": "source_customer_id",
    "order date (DateOrders)": "order_date", "shipping date (DateOrders)": "shipping_date",
    "Order Status": "order_status", "Delivery Status": "delivery_status",
    "Days for shipping (real)": "actual_days", "Days for shipment (scheduled)": "scheduled_days",
    "Shipping Mode": "shipping_mode", "Market": "market", "Order Region": "region",
    "Order Country": "country", "Category Id": "category_id", "Category Name": "category",
    "Product Card Id": "product_id", "Product Name": "product",
    "Order Item Quantity": "quantity", "Sales": "gross_sales",
    "Order Item Discount": "discount", "Order Item Total": "net_sales",
    "Order Profit Per Order": "profit", "Benefit per order": "benefit",
    "Order Item Profit Ratio": "profit_ratio", "Late_delivery_risk": "late_risk",
}


def clean(source: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    raw = pd.read_csv(source, encoding="latin1", low_memory=False)
    absent = set(FIELDS) - set(raw.columns)
    if absent:
        raise ValueError(f"Missing source columns: {sorted(absent)}")
    d = raw[list(FIELDS)].rename(columns=FIELDS).copy()
    for c in ["order_item_id", "order_id", "customer_id", "source_customer_id", "category_id", "product_id", "quantity", "actual_days", "scheduled_days", "late_risk"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in ["gross_sales", "discount", "net_sales", "profit", "benefit", "profit_ratio"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in ["order_date", "shipping_date"]:
        d[c] = pd.to_datetime(d[c], format="%m/%d/%Y %H:%M", errors="coerce")
    checks = {
        "source_rows": len(raw), "source_columns": len(raw.columns),
        "distinct_order_items": int(d.order_item_id.nunique()),
        "distinct_orders": int(d.order_id.nunique()),
        "distinct_customers": int(d.customer_id.nunique()),
        "duplicate_item_ids": int(d.order_item_id.duplicated().sum()),
        "customer_id_mismatches": int((d.customer_id != d.source_customer_id).sum()),
        "missing_order_dates": int(d.order_date.isna().sum()),
        "invalid_quantities": int((d.quantity <= 0).sum()),
        "financial_identity_failures": int(((d.gross_sales - d.discount - d.net_sales).abs() > .02).sum()),
        "profit_duplicate_failures": int(((d.profit - d.benefit).abs() > .02).sum()),
        "gross_sales_identity_failures": int(((d.quantity * pd.to_numeric(raw['Order Item Product Price'], errors='coerce') - d.gross_sales).abs() > .02).sum()),
    }
    stable = ["customer_id", "order_date", "shipping_date", "order_status", "delivery_status", "actual_days", "scheduled_days", "shipping_mode", "market", "region", "country"]
    checks["order_field_conflicts"] = {c: int((d.groupby("order_id")[c].nunique(dropna=False) > 1).sum()) for c in stable}
    fatal = ["duplicate_item_ids", "customer_id_mismatches", "financial_identity_failures", "profit_duplicate_failures", "gross_sales_identity_failures"]
    if any(checks[k] for k in fatal) or any(checks["order_field_conflicts"].values()):
        raise ValueError("Source failed validation; see checks: " + json.dumps(checks))
    if d[["order_id", "order_item_id", "customer_id"]].isna().any().any():
        raise ValueError("Missing key in source")
    items = d.drop(columns=["source_customer_id", "benefit", "profit_ratio", "late_risk"]).copy()
    items["financial_eligible"] = items.order_status.isin(FINISHED) & items.order_date.notna() & items.net_sales.notna() & (items.quantity > 0)
    # Summarize line amounts exactly once. Do not sum order attributes across items.
    first = items.sort_values("order_item_id").drop_duplicates("order_id")[stable + ["order_id"]].set_index("order_id")
    totals = items.groupby("order_id").agg(item_count=("order_item_id", "size"), gross_sales=("gross_sales", "sum"), discount=("discount", "sum"), net_sales=("net_sales", "sum"), profit=("profit", "sum"), units=("quantity", "sum"), all_lines_eligible=("financial_eligible", "all"))
    orders = first.join(totals).reset_index()
    orders["financial_eligible"] = orders.all_lines_eligible & orders.order_status.isin(FINISHED)
    orders["logistics_eligible"] = orders.financial_eligible & orders.delivery_status.ne("Shipping canceled") & orders.actual_days.notna() & orders.scheduled_days.notna() & (orders.actual_days >= 0) & (orders.scheduled_days >= 0)
    orders["delay_days"] = orders.actual_days - orders.scheduled_days
    orders["late"] = orders.logistics_eligible & (orders.delay_days > 0)
    checks["finished_item_rows"] = int(items.financial_eligible.sum())
    checks["finished_orders"] = int(orders.financial_eligible.sum())
    checks["logistics_eligible_orders"] = int(orders.logistics_eligible.sum())
    checks["source_net_sales"] = round(float(items.net_sales.sum()), 2)
    checks["finished_net_sales"] = round(float(items.loc[items.financial_eligible, "net_sales"].sum()), 2)
    checks["finished_profit"] = round(float(items.loc[items.financial_eligible, "profit"].sum()), 2)
    if not np.isclose(items.net_sales.sum(), orders.net_sales.sum(), atol=.02):
        raise AssertionError("Item and order sales do not reconcile")
    return items, orders, checks


def segment(orders: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    o = orders.loc[orders.financial_eligible].copy()
    snap = o.order_date.max().normalize() + pd.Timedelta(days=1)
    r = o.groupby("customer_id").agg(last_purchase=("order_date", "max"), first_purchase=("order_date", "min"), frequency=("order_id", "nunique"), monetary=("net_sales", "sum"))
    r["recency_days"] = (snap - r.last_purchase.dt.normalize()).dt.days
    r["average_order_value"] = r.monetary / r.frequency
    monetary_cut = r.monetary.quantile(.75)
    recency_cut = r.recency_days.median()
    inactive_cut = r.recency_days.quantile(.75)
    r["segment"] = np.select([
        (r.frequency >= 2) & (r.monetary >= monetary_cut) & (r.recency_days <= recency_cut),
        (r.frequency >= 2) & (r.recency_days >= inactive_cut),
        r.frequency >= 2,
        (r.frequency == 1) & (r.recency_days <= recency_cut),
    ], ["High-value repeat", "Inactive repeat", "Regular repeat", "Recent first-time"], default="Other first-time")
    r["snapshot_date"] = snap
    r = r.reset_index()
    o["cohort"] = o.groupby("customer_id").order_date.transform("min").dt.to_period("M")
    o["month"] = o.order_date.dt.to_period("M")
    o["month_index"] = (o.month.dt.year - o.cohort.dt.year) * 12 + o.month.dt.month - o.cohort.dt.month
    c = o.groupby(["cohort", "month_index"]).customer_id.nunique().rename("active_customers").reset_index()
    c["cohort_size"] = c.groupby("cohort").active_customers.transform("first")
    c["retention_rate"] = c.active_customers / c.cohort_size
    c["cohort"] = c.cohort.astype(str)
    return r, c


def summary(items: pd.DataFrame, orders: pd.DataFrame, rfm: pd.DataFrame) -> dict:
    i = items[items.financial_eligible]
    o = orders[orders.financial_eligible]
    l = orders[orders.logistics_eligible]
    first = o.sort_values(["order_date", "order_id"]).drop_duplicates("customer_id").order_id
    repeats = o[~o.order_id.isin(first)]
    return {
        "definition": "Finished states COMPLETE/CLOSED; observed net sales and recorded line profit; late = actual days > scheduled days on eligible orders",
        "net_sales": round(float(i.net_sales.sum()), 2), "profit": round(float(i.profit.sum()), 2),
        "profit_margin_pct": round(float(100 * i.profit.sum() / i.net_sales.sum()), 2),
        "orders": len(o), "customers": int(o.customer_id.nunique()),
        "average_order_value": round(float(o.net_sales.mean()), 2), "units": int(i.quantity.sum()),
        "loss_making_lines": int((i.profit < 0).sum()),
        "repeat_customers": int((rfm.frequency > 1).sum()),
        "repeat_customer_pct": round(float(100 * (rfm.frequency > 1).mean()), 2),
        "repeat_order_sales": round(float(repeats.net_sales.sum()), 2),
        "logistics_orders": len(l), "late_orders": int(l.late.sum()),
        "late_order_pct": round(float(100 * l.late.mean()), 2),
        "late_sales_exposure": round(float(l.loc[l.late, "net_sales"].sum()), 2),
        "snapshot_date": str(rfm.snapshot_date.iloc[0].date()),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=ROOT / "data/raw/DataCoSupplyChainDataset.csv")
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    items, orders, checks = clean(args.source)
    rfm, cohort = segment(orders)
    result = summary(items, orders, rfm)
    # Keep detailed customer and order exports local; do not commit these to a public repository.
    for name, frame in [("fact_order_items", items), ("fact_orders", orders), ("customer_rfm", rfm), ("cohort_retention", cohort)]:
        frame.to_csv(OUT / (name + ".csv"), index=False, float_format="%.6f")
    (ROOT / "docs/validation_results.json").write_text(json.dumps(checks, indent=2))
    (ROOT / "docs/kpi_results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"checks": checks, "kpis": result}, indent=2))


if __name__ == "__main__":
    main()
