"""Offline validation on provided CSVs when SQL Server is unavailable.

The primary deliverable workflow remains SQL -> Python -> Power BI.
"""
from pathlib import Path
import argparse
import json
import pandas as pd
from clickstream import compare_product_interest

ROOT = Path(__file__).resolve().parents[1]
cli = argparse.ArgumentParser()
cli.add_argument('--logs', type=Path, default=ROOT/'data/raw/tokenized_access_logs.csv')
cli.add_argument('--orders', type=Path, default=ROOT/'data/processed/fact_order_items.csv')
args = cli.parse_args()
raw = pd.read_csv(args.logs,encoding='utf-8-sig',usecols=['Date','Product'],low_memory=False)
raw['visit_date'] = pd.to_datetime(raw['Date'],format='%m/%d/%Y %H:%M',errors='raise').dt.normalize()
raw['product_key'] = raw.Product.str.strip().str.lower()
views = raw.groupby(['visit_date','product_key'],as_index=False).agg(product=('Product','first'),page_events=('Product','size'))
items = pd.read_csv(args.orders,parse_dates=['order_date'])
out, meta = compare_product_interest(views,items)
out.to_csv(ROOT/'data/processed/product_interest.csv',index=False)
(ROOT/'docs/clickstream_validation.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,indent=2))
