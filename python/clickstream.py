"""Compare product page events with sales in their overlapping calendar period.

Products match by normalized exact name only. No IP/customer join is possible.
"""
import pandas as pd


def compare_product_interest(views: pd.DataFrame, items: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    v = views.copy()
    v['visit_date'] = pd.to_datetime(v.visit_date, errors='raise').dt.normalize()
    v['product_key'] = v.product_key.astype(str).str.strip().str.lower()
    v['page_events'] = pd.to_numeric(v.page_events, errors='raise')
    earliest, latest = v.visit_date.min(), v.visit_date.max()
    if pd.isna(earliest):
        raise ValueError('No access log dates')
    a = items.copy()
    a['product_key'] = a['product'].astype(str).str.strip().str.lower()
    a['order_date'] = pd.to_datetime(a.order_date, errors='raise')
    all_keys = set(a.product_key.dropna())
    eligible = a[a.financial_eligible.astype(bool) & a.order_date.dt.normalize().between(earliest,latest)]
    sales = eligible.groupby('product_key').agg(completed_item_sales_in_window=('net_sales','sum'),
                                                completed_item_rows_in_window=('order_item_id','size')).reset_index()
    summary = v.groupby('product_key', as_index=False).agg(product=('product','first'),
                    page_events=('page_events','sum')).merge(sales,on='product_key',how='left')
    summary['matches_catalog_name'] = summary.product_key.isin(all_keys)
    summary[['completed_item_sales_in_window','completed_item_rows_in_window']] = summary[['completed_item_sales_in_window','completed_item_rows_in_window']].fillna(0)
    meta = {'page_events': int(v.page_events.sum()), 'logged_products': int(v.product_key.nunique()),
            'matched_catalog_names': int(summary.matches_catalog_name.sum()),
            'first_log_date': str(earliest.date()),'last_log_date':str(latest.date()),
            'meaning': 'Descriptive product-level event counts; no visit-to-order or customer attribution'}
    return summary.sort_values('page_events',ascending=False), meta
