"""SQL Server -> Python RFM/analysis -> SQL Server customer segments for Power BI.

Run after SQL scripts 01-03 with DATACO_ODBC_CONNECTION set.
Then run analyze.py, statistics.py, render_report.py, SQL scripts 04-07.
"""
import json
import os
from pathlib import Path
import pandas as pd

try:
    import pyodbc
except ImportError as exc:
    raise SystemExit('Install pyodbc and Microsoft ODBC Driver 18') from exc

from build import segment, summary
from clickstream import compare_product_interest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed'
conn_str = os.getenv('DATACO_ODBC_CONNECTION')
if not conn_str:
    raise SystemExit('Set DATACO_ODBC_CONNECTION before running this script')
OUT.mkdir(exist_ok=True, parents=True)

with pyodbc.connect(conn_str) as db:
    items = pd.read_sql_query('SELECT * FROM analytics.fact_order_items', db, parse_dates=['order_date','shipping_date'])
    orders = pd.read_sql_query('SELECT * FROM analytics.fact_orders', db, parse_dates=['order_date','shipping_date'])
    if items.order_item_id.duplicated().any() or orders.order_id.duplicated().any():
        raise AssertionError('SQL facts contain duplicate keys')
    if len(items) != orders.item_count.sum():
        raise AssertionError('SQL order item counts do not reconcile')
    if abs(items.net_sales.sum() - orders.net_sales.sum()) > .02:
        raise AssertionError('SQL line and order sales do not reconcile')
    # SQL bit columns can arrive as integers or bool; normalize before Python KPIs.
    for name in ('financial_eligible',):
        items[name] = items[name].astype(bool)
        orders[name] = orders[name].astype(bool)
    for name in ('logistics_eligible','late'):
        orders[name] = orders[name].astype(bool)
    rfm, cohort = segment(orders)
    for name, frame in [('fact_order_items', items), ('fact_orders', orders), ('customer_rfm', rfm), ('cohort_retention', cohort)]:
        frame.to_csv(OUT / f'{name}.csv', index=False, float_format='%.6f')
    kpis = summary(items, orders, rfm)
    (ROOT / 'docs/kpi_results.json').write_text(json.dumps(kpis, indent=2))

    if db.cursor().execute("SELECT OBJECT_ID('analytics.fact_product_views','U')").fetchval():
        views = pd.read_sql_query('SELECT visit_date,product_key,product,page_events FROM analytics.fact_product_views', db,
                                  parse_dates=['visit_date'])
        interest, meta = compare_product_interest(views, items)
        interest.to_csv(OUT / 'product_interest.csv', index=False)
        (ROOT / 'docs/clickstream_validation.json').write_text(json.dumps(meta,indent=2))
    else:
        raise RuntimeError('Run sql/08_clickstream.sql after importing access logs before Python analysis')

    # Return customer segmentation to SQL Server. SQL facts are the input;
    # Power BI can read the same SQL instance for facts and segment dimension.
    cur = db.cursor()
    cur.execute('DELETE FROM analytics.customer_rfm')
    cur.fast_executemany = True
    cols = ('customer_id','last_purchase','first_purchase','frequency','monetary',
            'recency_days','average_order_value','segment','snapshot_date')
    insert = ('INSERT INTO analytics.customer_rfm (' + ','.join(cols) + ') VALUES ('
              + ','.join('?' for _ in cols) + ')')
    for start in range(0, len(rfm), 200):
        rows = []
        for row in rfm.iloc[start:start+200][list(cols)].itertuples(index=False, name=None):
            rows.append(tuple(v.to_pydatetime() if isinstance(v, pd.Timestamp) else
                              v.item() if hasattr(v, 'item') else v for v in row))
        cur.executemany(insert, rows)
    loaded = cur.execute('SELECT COUNT(*) FROM analytics.customer_rfm').fetchval()
    if loaded != len(rfm):
        db.rollback()
        raise AssertionError(f'RFM writeback mismatch: {loaded} != {len(rfm)}')
    db.commit()
    print(json.dumps({'source': 'SQL Server facts', 'rfm_customers': loaded,
                      'finished_orders': kpis['orders'], 'late_orders': kpis['late_orders'],
                      'clickstream_events': meta['page_events']}, indent=2))
