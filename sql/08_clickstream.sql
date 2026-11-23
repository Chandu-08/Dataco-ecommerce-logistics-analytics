-- Run after importing tokenized_access_logs.csv with --dataset logs.
-- Page events can be compared with products, but have no customer/order key.
USE DataCo_Analytics;
GO
IF OBJECT_ID('staging.DataCoAccessLogs','U') IS NULL THROW 50010, 'Import access logs into staging.DataCoAccessLogs first.', 1;
IF OBJECT_ID('clean.access_events','U') IS NOT NULL DROP TABLE clean.access_events;
SELECT source_row_id,
 TRY_CONVERT(datetime2(0),[Date],101) event_at,
 NULLIF(LTRIM(RTRIM([Product])), '') product,
 LOWER(NULLIF(LTRIM(RTRIM([Product])), '')) product_key,
 NULLIF(LTRIM(RTRIM([Category])), '') category,
 NULLIF(LTRIM(RTRIM([Department])), '') department
INTO clean.access_events FROM staging.DataCoAccessLogs;
-- Drop IP-like identifiers and URLs from the analytical clickstream table.
IF EXISTS (SELECT 1 FROM clean.access_events WHERE event_at IS NULL OR product_key IS NULL)
 THROW 50011, 'Access log date or product did not parse. Review staging rows.', 1;
IF OBJECT_ID('analytics.fact_product_views','U') IS NOT NULL DROP TABLE analytics.fact_product_views;
SELECT CAST(event_at AS date) visit_date,
 product_key, MIN(product) product,
 COUNT_BIG(*) page_events
INTO analytics.fact_product_views FROM clean.access_events
GROUP BY CAST(event_at AS date),product_key;
CREATE UNIQUE CLUSTERED INDEX IX_product_views ON analytics.fact_product_views(visit_date,product_key);
SELECT (SELECT COUNT_BIG(*) FROM staging.DataCoAccessLogs) staged_events,
       (SELECT COUNT_BIG(*) FROM clean.access_events) cleaned_events,
       (SELECT SUM(page_events) FROM analytics.fact_product_views) aggregated_events;
SELECT MIN(visit_date) first_log_date, MAX(visit_date) last_log_date,
 COUNT(DISTINCT product_key) logged_products FROM analytics.fact_product_views;
-- Product match is descriptive; event count is not customers, sales, or conversion.
WITH sale_products AS (
 SELECT DISTINCT LOWER(LTRIM(RTRIM(product))) product_key
 FROM analytics.fact_order_items WHERE product IS NOT NULL
)
SELECT COUNT(DISTINCT v.product_key) logged_products,
 COUNT(DISTINCT CASE WHEN s.product_key IS NOT NULL THEN v.product_key END) matched_product_names
FROM analytics.fact_product_views v LEFT JOIN sale_products s ON s.product_key=v.product_key;
GO
CREATE OR ALTER VIEW analytics.vw_product_interest AS
WITH log_window AS (
 SELECT MIN(visit_date) first_day, MAX(visit_date) last_day FROM analytics.fact_product_views
), views AS (
 SELECT product_key, MIN(product) product, SUM(page_events) page_events
 FROM analytics.fact_product_views GROUP BY product_key
), sales AS (
 SELECT LOWER(LTRIM(RTRIM(i.product))) product_key, SUM(i.net_sales) completed_item_sales_in_window,
 COUNT_BIG(*) completed_item_rows_in_window
 FROM analytics.fact_order_items i CROSS JOIN log_window w
 WHERE i.financial_eligible=1 AND CAST(i.order_date AS date) BETWEEN w.first_day AND w.last_day
 GROUP BY LOWER(LTRIM(RTRIM(i.product)))
)
SELECT v.product_key,v.product,v.page_events,
 COALESCE(s.completed_item_sales_in_window,0) completed_item_sales_in_window,
 COALESCE(s.completed_item_rows_in_window,0) completed_item_rows_in_window
FROM views v LEFT JOIN sales s ON s.product_key=v.product_key;
GO
