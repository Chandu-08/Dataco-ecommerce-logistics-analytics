"""Offline four-page HTML dashboard built from verified aggregate outputs."""
from pathlib import Path
from base64 import b64encode
from html import escape
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
K = json.loads((ROOT / "docs/kpi_results.json").read_text())
D = ROOT / "data/processed"


def table(file, cols, limit=8):
    x = pd.read_csv(D / (file + ".csv")).head(limit)
    rows = ''.join('<tr>' + ''.join(f'<td>{escape(str(round(v, 2) if isinstance(v, float) else v))}</td>' for v in row) + '</tr>' for row in x[cols].itertuples(index=False, name=None))
    return '<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{escape(c.replace("_", " ").title())}</th>' for c in cols) + '</tr></thead><tbody>' + rows + '</tbody></table></div>'


def img(name, alt):
    s = b64encode((ROOT / "dashboards" / name).read_bytes()).decode()
    return f'<img alt="{escape(alt)}" src="data:image/png;base64,{s}">'


def card(label, val):
    return f'<div class="card"><small>{escape(label)}</small><strong>{escape(str(val))}</strong></div>'


pages = [
 ('Executive', '<div class="cards">' + card('Recorded net sales', f'{K["net_sales"]:,.2f}') + card('Recorded profit', f'{K["profit"]:,.2f}') + card('Margin', f'{K["profit_margin_pct"]}%') + card('Finished orders', f'{K["orders"]:,}') + '</div><div class="grid">' + img('monthly_sales.png', 'Monthly sales') + '<div><h2>Leading categories</h2>' + table('financial_by_category', ['category','sales','profit','margin_pct']) + '</div></div>'),
 ('Customers', '<div class="cards">' + card('Finished-order customers', f'{K["customers"]:,}') + card('Repeat customers', f'{K["repeat_customers"]:,}') + card('Repeat share', f'{K["repeat_customer_pct"]}%') + '</div><div class="grid">' + img('segments.png', 'Sales by customer segment') + '<div><h2>RFM segments</h2>' + table('segment_summary', ['segment','customers','sales','mean_orders','mean_recency']) + '</div></div>'),
 ('Logistics', '<div class="cards">' + card('Eligible orders', f'{K["logistics_orders"]:,}') + card('Late orders', f'{K["late_orders"]:,}') + card('Late rate', f'{K["late_order_pct"]}%') + '</div><div class="grid">' + img('shipping_mode.png', 'Late rate by shipping mode') + '<div><h2>Mode comparison</h2>' + table('logistics_by_shipping_mode', ['shipping_mode','orders','late_orders','late_pct','late_sales_exposure']) + '</div></div>'),
 ('Decisions', '<div class="cards">' + card('Sales associated with late orders', f'{K["late_sales_exposure"]:,.2f}') + card('Loss-making item rows', f'{K["loss_making_lines"]:,}') + '</div><div class="grid"><div><h2>Where to investigate</h2>' + table('logistics_by_market', ['market','orders','late_orders','late_pct','late_sales_exposure']) + '</div><div><h2>Recommended checks</h2><p>Audit First Class promise-day definitions and shipment timestamps; compare like-for-like lanes and order mixes before changing shipping policies.</p><p>Investigate margin and discounts in high-volume categories. Test any change with tracked late-order rate, profit margin, and delivery costs.</p><p>Sales exposure is booked sales on late orders, not proven lost revenue. Currency is unspecified in the source.</p></div></div>' + ('<div class="grid">' + img('product_interest.png', 'Most viewed products') + '<div><h2>Product interest during log window</h2>' + table('product_interest', ['product','page_events','completed_item_sales_in_window'], 8) + '<p>Page events are not unique customers or purchases; product name matches are descriptive.</p></div></div>' if (D / 'product_interest.csv').exists() and (ROOT / 'dashboards/product_interest.png').exists() else '')),
]
nav = ''.join(f'<button onclick="show({i})">{escape(name)}</button>' for i, (name, _) in enumerate(pages))
sections = ''.join(f'<section id="p{i}" style="display:{"block" if i==0 else "none"}"><h1>{escape(name)}</h1>{content}</section>' for i, (name, content) in enumerate(pages))
html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DataCo decision analytics</title><style>
body{font:16px system-ui,sans-serif;background:#f3f6f7;color:#183147;margin:0}header{background:#102d3e;color:white;padding:24px max(20px,5vw)}header p{color:#c5d5de}nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}button{border:1px solid #aac5d0;border-radius:6px;color:#fff;background:#24566b;padding:9px 15px;cursor:pointer}main{max-width:1260px;margin:auto;padding:26px}.cards{display:flex;flex-wrap:wrap;gap:14px;margin:20px 0}.card{background:white;border:1px solid #dce7e9;padding:18px;border-radius:10px;min-width:160px;flex:1}.card small{display:block;color:#596d76}.card strong{font-size:26px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.grid>img,.grid>div{background:#fff;width:100%;box-sizing:border-box;padding:16px;border-radius:10px;box-shadow:0 1px 4px #d4e0e4}img{object-fit:contain}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px 8px;text-align:left;border-bottom:1px solid #e0e8eb}th{background:#eaf1f4}.scroll{overflow-x:auto}footer{padding:20px;color:#51636b}@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style><header><strong>DataCo / Decision Analytics</strong><p>Observed transactions • finished statuses COMPLETE and CLOSED • order-level delivery denominator</p><nav>''' + nav + '</nav></header><main>' + sections + '</main><footer>Analytical portfolio exercise. Dataset: DataCo Smart Supply Chain (CC BY 4.0). Figures describe the source data; they do not establish business impact.</footer><script>function show(n){document.querySelectorAll("section").forEach((p,i)=>p.style.display=i===n?"block":"none")}</script></html>'
(ROOT / "dashboards/four_page_report.html").write_text(html, encoding="utf-8")
print('Rendered four-page offline report')
