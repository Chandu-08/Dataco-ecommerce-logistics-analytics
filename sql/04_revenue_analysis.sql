USE DataCo_Analytics;
GO
-- Executive: join only after aggregation at the relevant grain.
WITH item_kpis AS (
 SELECT SUM(net_sales) sales, SUM(profit) profit, SUM(discount) discount, SUM(quantity) units,
 SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) loss_lines
 FROM analytics.vw_finished_items
), order_kpis AS (
 SELECT COUNT(*) orders, COUNT(DISTINCT customer_id) customers, AVG(net_sales) average_order_value
 FROM analytics.vw_finished_orders
)
SELECT i.*, o.*, 100.0 * i.profit / NULLIF(i.sales,0) AS margin_pct
FROM item_kpis i CROSS JOIN order_kpis o;
WITH c AS (
 SELECT category, SUM(net_sales) sales, SUM(profit) profit
 FROM analytics.vw_finished_items GROUP BY category
)
SELECT *, 100.0 * profit / NULLIF(sales,0) AS margin_pct,
 RANK() OVER (ORDER BY sales DESC) AS revenue_rank,
 SUM(sales) OVER () AS all_category_sales
FROM c ORDER BY sales DESC;
SELECT market, region, SUM(net_sales) sales, SUM(profit) profit,
 100.0*SUM(profit)/NULLIF(SUM(net_sales),0) margin_pct
FROM analytics.vw_finished_items GROUP BY market, region ORDER BY sales DESC;
WITH m AS (
 SELECT DATEFROMPARTS(YEAR(order_date),MONTH(order_date),1) month_start,
 SUM(net_sales) sales, SUM(profit) profit FROM analytics.vw_finished_items
 GROUP BY DATEFROMPARTS(YEAR(order_date),MONTH(order_date),1)
)
SELECT *, LAG(sales) OVER(ORDER BY month_start) previous_month_sales,
 100.0*(sales-LAG(sales) OVER(ORDER BY month_start))/NULLIF(LAG(sales) OVER(ORDER BY month_start),0) mom_pct
FROM m ORDER BY month_start;
SELECT CASE WHEN gross_sales = 0 THEN 'undefined'
 WHEN discount/gross_sales < .05 THEN 'under 5%'
 WHEN discount/gross_sales < .20 THEN '5-20%' ELSE '20%+' END discount_band,
 COUNT(*) items, SUM(net_sales) sales, SUM(profit) profit
FROM analytics.vw_finished_items GROUP BY CASE WHEN gross_sales = 0 THEN 'undefined'
 WHEN discount/gross_sales < .05 THEN 'under 5%' WHEN discount/gross_sales < .20 THEN '5-20%' ELSE '20%+' END;
