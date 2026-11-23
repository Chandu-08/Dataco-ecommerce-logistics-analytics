-- Run after python/import_raw_sql_server.py. Preserve original values in staging.DataCoRaw.
USE DataCo_Analytics;
GO
IF OBJECT_ID('staging.DataCoRaw','U') IS NULL THROW 50001, 'Import original CSV into staging.DataCoRaw first.', 1;
IF OBJECT_ID('clean.order_items','U') IS NOT NULL DROP TABLE clean.order_items;
SELECT source_row_id,
 TRY_CONVERT(bigint,[Order Item Id]) order_item_id,
 TRY_CONVERT(bigint,[Order Id]) order_id,
 TRY_CONVERT(bigint,[Order Customer Id]) customer_id,
 TRY_CONVERT(bigint,[Customer Id]) source_customer_id,
 TRY_CONVERT(datetime2(0),[order date (DateOrders)],101) order_date,
 TRY_CONVERT(datetime2(0),[shipping date (DateOrders)],101) shipping_date,
 NULLIF(LTRIM(RTRIM([Order Status])), '') order_status,
 NULLIF(LTRIM(RTRIM([Delivery Status])), '') delivery_status,
 TRY_CONVERT(int,[Days for shipping (real)]) actual_days,
 TRY_CONVERT(int,[Days for shipment (scheduled)]) scheduled_days,
 NULLIF(LTRIM(RTRIM([Shipping Mode])), '') shipping_mode,
 NULLIF(LTRIM(RTRIM([Market])), '') market,
 NULLIF(LTRIM(RTRIM([Order Region])), '') region,
 NULLIF(LTRIM(RTRIM([Order Country])), '') country,
 TRY_CONVERT(int,[Category Id]) category_id,
 NULLIF(LTRIM(RTRIM([Category Name])), '') category,
 TRY_CONVERT(bigint,[Product Card Id]) product_id,
 NULLIF(LTRIM(RTRIM([Product Name])), '') product,
 TRY_CONVERT(int,[Order Item Quantity]) quantity,
 TRY_CONVERT(float,[Order Item Product Price]) unit_price,
 TRY_CONVERT(float,[Sales]) gross_sales,
 TRY_CONVERT(float,[Order Item Discount]) discount,
 TRY_CONVERT(float,[Order Item Total]) net_sales,
 TRY_CONVERT(float,[Order Profit Per Order]) profit,
 TRY_CONVERT(float,[Benefit per order]) benefit,
 TRY_CONVERT(int,[Late_delivery_risk]) late_risk
INTO clean.order_items FROM staging.DataCoRaw;
-- Customer names, email, password and street do not enter clean or analytics.
IF EXISTS (SELECT 1 FROM clean.order_items WHERE order_item_id IS NULL OR order_id IS NULL OR customer_id IS NULL)
 THROW 50002, 'Missing or invalid analytical key. Inspect staged rows.', 1;
IF EXISTS (SELECT 1 FROM clean.order_items GROUP BY order_item_id HAVING COUNT(*)>1)
 THROW 50003, 'Duplicate order-item key. Review staged rows.', 1;
IF EXISTS (SELECT 1 FROM clean.order_items WHERE customer_id <> source_customer_id OR source_customer_id IS NULL)
 THROW 50004, 'Customer IDs disagree or are missing.', 1;
IF EXISTS (SELECT 1 FROM clean.order_items WHERE quantity IS NULL OR quantity<=0 OR order_date IS NULL)
 THROW 50005, 'Invalid quantity or order date. Review before transformation.', 1;
IF EXISTS (SELECT 1 FROM clean.order_items WHERE gross_sales IS NULL OR discount IS NULL OR net_sales IS NULL OR profit IS NULL OR benefit IS NULL OR unit_price IS NULL
 OR ABS(gross_sales-discount-net_sales)>.02 OR ABS(quantity*unit_price-gross_sales)>.02 OR ABS(profit-benefit)>.02)
 THROW 50006, 'Financial parse or reconciliation failed.', 1;
CREATE UNIQUE CLUSTERED INDEX IX_clean_item ON clean.order_items(order_item_id);
CREATE INDEX IX_clean_order ON clean.order_items(order_id);
SELECT COUNT_BIG(*) raw_rows FROM staging.DataCoRaw;
SELECT COUNT_BIG(*) clean_rows, COUNT(DISTINCT order_item_id) item_ids,
 COUNT(DISTINCT order_id) orders, COUNT(DISTINCT customer_id) customers,
 SUM(net_sales) all_status_sales FROM clean.order_items;
SELECT order_status, delivery_status, COUNT_BIG(*) item_rows FROM clean.order_items
GROUP BY order_status, delivery_status ORDER BY item_rows DESC;
GO
