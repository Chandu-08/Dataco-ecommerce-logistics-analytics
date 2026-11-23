USE DataCo_Analytics;
GO
SELECT 'items' metric, COUNT(*) value FROM analytics.fact_order_items
UNION ALL SELECT 'orders', COUNT(*) FROM analytics.fact_orders
UNION ALL SELECT 'customers_rfm', COUNT(*) FROM analytics.customer_rfm;
SELECT SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END) AS unmatched_order_lines
FROM analytics.fact_order_items i LEFT JOIN analytics.fact_orders o ON o.order_id=i.order_id
WHERE o.order_id IS NULL;
SELECT (SELECT SUM(net_sales) FROM analytics.vw_finished_items) AS item_sales,
       (SELECT SUM(net_sales) FROM analytics.vw_finished_orders) AS order_sales;
SELECT (SELECT COUNT(*) FROM analytics.fact_orders WHERE logistics_eligible=1 AND late=1) late_orders,
       (SELECT COUNT(*) FROM analytics.fact_orders WHERE logistics_eligible=1) eligible_orders;
SELECT (SELECT COUNT_BIG(*) FROM staging.DataCoRaw) raw_rows,
       (SELECT COUNT_BIG(*) FROM clean.order_items) clean_rows,
       (SELECT COUNT_BIG(*) FROM analytics.fact_order_items) item_fact_rows;
SELECT COUNT(DISTINCT customer_id) finished_customers FROM analytics.fact_orders WHERE financial_eligible=1;
SELECT COUNT(*) rfm_customers FROM analytics.customer_rfm;
SELECT COUNT(*) invalid_delivery_flags FROM analytics.fact_orders
WHERE logistics_eligible=1 AND ((late=1 AND actual_days<=scheduled_days) OR (late=0 AND actual_days>scheduled_days));
SELECT (SELECT COUNT_BIG(*) FROM staging.DataCoAccessLogs) staged_access_events,
       (SELECT COUNT_BIG(*) FROM clean.access_events) cleaned_access_events,
       (SELECT SUM(page_events) FROM analytics.fact_product_views) aggregated_access_events;
