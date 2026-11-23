-- In SSMS, create database if necessary, then run this entire file in DataCo_Analytics.
IF DB_ID(N'DataCo_Analytics') IS NULL CREATE DATABASE DataCo_Analytics;
GO
USE DataCo_Analytics;
GO
IF SCHEMA_ID(N'analytics') IS NULL EXEC(N'CREATE SCHEMA analytics');
IF SCHEMA_ID(N'staging') IS NULL EXEC(N'CREATE SCHEMA staging');
IF SCHEMA_ID(N'clean') IS NULL EXEC(N'CREATE SCHEMA clean');
GO
IF OBJECT_ID('analytics.fact_order_items','U') IS NULL
CREATE TABLE analytics.fact_order_items (
 order_item_id bigint NOT NULL PRIMARY KEY, order_id bigint NOT NULL, customer_id bigint NOT NULL,
 order_date datetime2 NULL, shipping_date datetime2 NULL, order_status nvarchar(50), delivery_status nvarchar(50),
 actual_days int NULL, scheduled_days int NULL, shipping_mode nvarchar(50), market nvarchar(80), region nvarchar(120), country nvarchar(120),
 category_id int, category nvarchar(120), product_id bigint, product nvarchar(300), quantity int,
 gross_sales float, discount float, net_sales float, profit float, financial_eligible bit NOT NULL
);
IF OBJECT_ID('analytics.fact_orders','U') IS NULL
CREATE TABLE analytics.fact_orders (
 order_id bigint NOT NULL PRIMARY KEY, customer_id bigint NOT NULL, order_date datetime2, shipping_date datetime2,
 order_status nvarchar(50), delivery_status nvarchar(50), actual_days int, scheduled_days int,
 shipping_mode nvarchar(50), market nvarchar(80), region nvarchar(120), country nvarchar(120), item_count int,
 gross_sales float, discount float, net_sales float, profit float, units int,
 financial_eligible bit NOT NULL, logistics_eligible bit NOT NULL, delay_days int, late bit NOT NULL
);
IF OBJECT_ID('analytics.customer_rfm','U') IS NULL
CREATE TABLE analytics.customer_rfm (
 customer_id bigint NOT NULL PRIMARY KEY, last_purchase datetime2, first_purchase datetime2,
 frequency int, monetary float, recency_days int, average_order_value float,
 segment nvarchar(80), snapshot_date date
);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('analytics.fact_order_items') AND name='IX_items_order') CREATE INDEX IX_items_order ON analytics.fact_order_items(order_id);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('analytics.fact_order_items') AND name='IX_items_date_category') CREATE INDEX IX_items_date_category ON analytics.fact_order_items(order_date, category);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('analytics.fact_orders') AND name='IX_orders_date') CREATE INDEX IX_orders_date ON analytics.fact_orders(order_date);
GO
