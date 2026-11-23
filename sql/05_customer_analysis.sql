USE DataCo_Analytics;
GO
SELECT segment, COUNT(*) customers, SUM(monetary) sales, AVG(CAST(frequency AS float)) mean_orders,
 AVG(CAST(recency_days AS float)) mean_recency
FROM analytics.customer_rfm GROUP BY segment ORDER BY sales DESC;
WITH ranked AS (
 SELECT customer_id, monetary, frequency, DENSE_RANK() OVER(ORDER BY monetary DESC) AS spending_rank,
 ROW_NUMBER() OVER(ORDER BY monetary DESC, customer_id) AS row_number
 FROM analytics.customer_rfm
)
SELECT * FROM ranked WHERE row_number <= 20 ORDER BY row_number;
SELECT COUNT(*) customers, SUM(CASE WHEN frequency > 1 THEN 1 ELSE 0 END) repeat_customers,
 100.0 * SUM(CASE WHEN frequency > 1 THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0) repeat_pct
FROM analytics.customer_rfm;
