USE DataCo_Analytics;
GO
WITH eligible AS (SELECT * FROM analytics.fact_orders WHERE logistics_eligible = 1)
SELECT COUNT(*) orders, SUM(CAST(late AS int)) late_orders,
 100.0*SUM(CAST(late AS int))/NULLIF(COUNT(*),0) late_pct,
 AVG(CAST(actual_days AS float)) actual_days, AVG(CAST(scheduled_days AS float)) scheduled_days,
 AVG(CASE WHEN late=1 THEN CAST(delay_days AS float) END) positive_delay_days,
 SUM(CASE WHEN late=1 THEN net_sales ELSE 0 END) late_sales_exposure
FROM eligible;
SELECT shipping_mode, COUNT(*) orders, SUM(CAST(late AS int)) late_orders,
 100.0*SUM(CAST(late AS int))/NULLIF(COUNT(*),0) late_pct,
 AVG(CAST(actual_days AS float)) actual_days, AVG(CAST(scheduled_days AS float)) scheduled_days,
 SUM(CASE WHEN late=1 THEN net_sales ELSE 0 END) late_sales_exposure
FROM analytics.fact_orders WHERE logistics_eligible=1
GROUP BY shipping_mode ORDER BY late_orders DESC;
SELECT market, region, COUNT(*) orders, SUM(CAST(late AS int)) late_orders,
 100.0*SUM(CAST(late AS int))/NULLIF(COUNT(*),0) late_pct,
 SUM(CASE WHEN late=1 THEN net_sales ELSE 0 END) late_sales_exposure
FROM analytics.fact_orders WHERE logistics_eligible=1
GROUP BY market, region ORDER BY late_orders DESC;
-- Distinct order-category membership; totals across categories can exceed total orders.
SELECT i.category, COUNT(DISTINCT i.order_id) AS orders_with_category,
 COUNT(DISTINCT CASE WHEN o.late=1 THEN i.order_id END) AS late_orders_with_category
FROM analytics.fact_order_items i JOIN analytics.fact_orders o ON o.order_id=i.order_id
WHERE o.logistics_eligible=1 GROUP BY i.category ORDER BY late_orders_with_category DESC;
