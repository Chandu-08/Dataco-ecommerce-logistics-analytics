-- Populate facts entirely from SQL-cleaned staging. Run after 02_data_cleaning.sql.
USE DataCo_Analytics;
GO
SET XACT_ABORT ON;
IF OBJECT_ID('clean.order_items','U') IS NULL THROW 50007, 'Run SQL cleaning first.', 1;
IF EXISTS (
 SELECT 1 FROM clean.order_items GROUP BY order_id HAVING
 COUNT(DISTINCT ISNULL(CONVERT(nvarchar(30),customer_id),'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(CONVERT(nvarchar(30),order_date,126),'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(CONVERT(nvarchar(30),shipping_date,126),'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(order_status,'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(delivery_status,'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(CONVERT(nvarchar(20),actual_days),'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(CONVERT(nvarchar(20),scheduled_days),'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(shipping_mode,'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(market,'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(region,'[NULL]'))>1 OR
 COUNT(DISTINCT ISNULL(country,'[NULL]'))>1
) THROW 50008, 'An order has conflicting customer, date, status, shipping or geography fields.', 1;
BEGIN TRANSACTION;
DELETE FROM analytics.fact_order_items;
DELETE FROM analytics.fact_orders;
INSERT INTO analytics.fact_order_items (
 order_item_id,order_id,customer_id,order_date,shipping_date,order_status,delivery_status,
 actual_days,scheduled_days,shipping_mode,market,region,country,category_id,category,
 product_id,product,quantity,gross_sales,discount,net_sales,profit,financial_eligible)
SELECT order_item_id,order_id,customer_id,order_date,shipping_date,order_status,delivery_status,
 actual_days,scheduled_days,shipping_mode,market,region,country,category_id,category,
 product_id,product,quantity,gross_sales,discount,net_sales,profit,
 CASE WHEN order_status IN ('COMPLETE','CLOSED') AND order_date IS NOT NULL AND net_sales IS NOT NULL AND quantity>0 THEN 1 ELSE 0 END
FROM clean.order_items;
WITH rolls AS (
 SELECT order_id, MIN(customer_id) customer_id, MIN(order_date) order_date,
 MIN(shipping_date) shipping_date, MIN(order_status) order_status, MIN(delivery_status) delivery_status,
 MIN(actual_days) actual_days, MIN(scheduled_days) scheduled_days, MIN(shipping_mode) shipping_mode,
 MIN(market) market, MIN(region) region, MIN(country) country,
 COUNT(*) item_count, SUM(gross_sales) gross_sales, SUM(discount) discount,
 SUM(net_sales) net_sales, SUM(profit) profit, SUM(quantity) units,
 MIN(CAST(financial_eligible AS int)) all_lines_eligible
 FROM analytics.fact_order_items GROUP BY order_id)
INSERT INTO analytics.fact_orders (
 order_id,customer_id,order_date,shipping_date,order_status,delivery_status,
 actual_days,scheduled_days,shipping_mode,market,region,country,item_count,
 gross_sales,discount,net_sales,profit,units,financial_eligible,logistics_eligible,delay_days,late)
SELECT order_id,customer_id,order_date,shipping_date,order_status,delivery_status,
 actual_days,scheduled_days,shipping_mode,market,region,country,item_count,
 gross_sales,discount,net_sales,profit,units,all_lines_eligible,
 CASE WHEN all_lines_eligible=1 AND delivery_status<>'Shipping canceled' AND actual_days>=0 AND scheduled_days>=0 THEN 1 ELSE 0 END,
 CASE WHEN actual_days IS NOT NULL AND scheduled_days IS NOT NULL THEN actual_days-scheduled_days ELSE NULL END,
 CASE WHEN all_lines_eligible=1 AND delivery_status<>'Shipping canceled' AND actual_days>=0 AND scheduled_days>=0 AND actual_days>scheduled_days THEN 1 ELSE 0 END
FROM rolls;
IF (SELECT COUNT_BIG(*) FROM analytics.fact_order_items)<>(SELECT COUNT_BIG(*) FROM clean.order_items)
 OR EXISTS (SELECT 1 FROM analytics.fact_orders o LEFT JOIN analytics.fact_order_items i ON i.order_id=o.order_id
 GROUP BY o.order_id,o.item_count,o.net_sales HAVING COUNT_BIG(i.order_item_id)<>o.item_count OR ABS(SUM(i.net_sales)-o.net_sales)>.02)
BEGIN
 ROLLBACK TRANSACTION;
 THROW 50009, 'Source-to-fact row or order-finance reconciliation failed.', 1;
END;
COMMIT TRANSACTION;
GO
CREATE OR ALTER VIEW analytics.dim_customers AS
 SELECT customer_id, segment, first_purchase, last_purchase, frequency, monetary, recency_days
 FROM analytics.customer_rfm;
GO
CREATE OR ALTER VIEW analytics.dim_products AS
 SELECT product_id, MAX(product) product, MAX(category_id) category_id, MAX(category) category
 FROM analytics.fact_order_items WHERE product_id IS NOT NULL GROUP BY product_id;
GO
CREATE OR ALTER VIEW analytics.vw_finished_orders AS
 SELECT * FROM analytics.fact_orders WHERE financial_eligible=1;
GO
CREATE OR ALTER VIEW analytics.vw_finished_items AS
 SELECT * FROM analytics.fact_order_items WHERE financial_eligible=1;
GO
