# Run the complete SQL Server → Python → Power BI pipeline

## 0. Input and software

Place the three uploaded CSVs in `data/raw/`: `DataCoSupplyChainDataset.csv`, `DescriptionDataCoSupplyChain.csv`, and `tokenized_access_logs.csv`. The order CSV is Latin-1 encoded and access logs are UTF-8; the importer handles both. The description CSV is the reference for order fields. Install SQL Server, SSMS, a compatible Microsoft ODBC Driver for SQL Server, and Python packages in `requirements.txt`. Run commands from the project root. Use a local database account that can create schemas and tables in `DataCo_Analytics`; never commit a connection string with credentials.

For a Windows PowerShell session using integrated authentication (adjust `SERVER` for your machine):

```powershell
py -m pip install -r requirements.txt
$env:DATACO_ODBC_CONNECTION = 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=DataCo_Analytics;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes'
```

## 1. SQL Server database and CSV upload

Open `sql/01_database_setup.sql` in SSMS and execute it. It creates the database, schemas and empty analytics tables. Then run:

```powershell
py python/import_raw_sql_server.py --dataset orders --csv data/raw/DataCoSupplyChainDataset.csv
py python/import_raw_sql_server.py --dataset logs --csv data/raw/tokenized_access_logs.csv
```

The script creates `staging.DataCoRaw` with 53 original order fields and `staging.DataCoAccessLogs` with 8 original log fields, then imports records as text in 200-row batches. It checks the CSV field count, cell width and imported row count. Expect **180,519 order rows** and **469,977 log events**. Staging includes sensitive source fields (including `Customer Password` and IP-like fields); restrict access. A second import stops rather than duplicating rows. Only use `--replace` when an intentional re-import is required.

## 2. Cleaning and transformations in SQL Server

Execute `sql/02_data_cleaning.sql` in SSMS. This creates `clean.order_items` by parsing source text with `TRY_CONVERT`, trimming categorical values, and selecting non-PII fields. It fails on invalid keys, duplicate item IDs, invalid quantity/date, or unreconciled sales/profit. Negative profit remains valid. Inspect the last three result sets: expect **180,519 raw and clean rows**, **65,752 distinct orders**, and **20,652 distinct source customers**.

Execute `sql/03_dimensional_model.sql` in SSMS. This checks that customer, order, shipping and geography fields are constant within an order. It then builds `analytics.fact_order_items` (one row per item) and `analytics.fact_orders` (one row per order), and reconciles counts and order sales before committing. `financial_eligible` means `COMPLETE` or `CLOSED`; `logistics_eligible` requires valid shipping days and an uncanceled delivery. `late` is actual shipping days greater than scheduled days. Expect **79,107 eligible item rows** and **28,965 eligible orders**. The source has 53 columns, but clean and analytics intentionally omit the personal fields.

Execute `sql/08_clickstream.sql` in SSMS. It parses log dates, removes IP-like fields from the analytical layer, and groups events by product and day into `analytics.fact_product_views`. Expect **469,977 events**, **76 logged product names**, **72 matched to the order catalog** after name normalization, and an observation window of **2017-09-01 through 2018-01-31**. No order/customer ID exists in logs. Product comparisons are descriptive; do not calculate customer conversion from this table.

## 3. Python reads SQL and returns RFM segments

Run:

```powershell
py python/after_sql.py
py python/analyze.py
py python/statistics.py
py python/render_report.py
```

`after_sql.py` queries the two SQL fact tables plus product event aggregates, validates key uniqueness and item/order net sales, calculates RFM and purchase cohorts from **distinct completed orders**, then inserts **14,543** customer segment records into `analytics.customer_rfm`. It also compares product event counts with completed item sales in the **same log date window** by normalized product name. `analyze.py` creates market/category/mode aggregates and a product-interest chart; `statistics.py` generates order-level mode intervals; `render_report.py` creates the offline HTML report. Customer-level CSVs stay local and are excluded from the shared ZIP.

## 4. SQL validation

Run `sql/04_revenue_analysis.sql`, `sql/05_customer_analysis.sql`, `sql/06_logistics_analysis.sql`, and `sql/07_data_validation.sql` in SSMS. Check source, clean and item fact row counts agree; item and order net sales match to 0.02; no unmatched order lines; 14,543 RFM customers agree with distinct finished-order customer count; no invalid delivery flags; log events reconcile from staging to aggregate. Compare KPI values with `docs/kpi_results.json`: finished net sales **14,476,738.58**, recorded profit **1,779,716.84**, eligible shipping orders **28,965**, late orders **16,633**. Amounts have no confirmed currency.

If an early validation fails, inspect the implicated staging `source_row_id` and the source CSV. Fix source interpretation or import code and rerun from staging; do not delete anomalous business records merely to force totals. The project's measured figures are from a Python-only check against the actual CSV. SQL execution must be completed on a SQL Server installation and should be reconciled against these values.

## 5. Power BI reads the resulting SQL tables

Connect Power BI Desktop to database `DataCo_Analytics`. Import `analytics.fact_orders`, `analytics.fact_order_items`, `analytics.customer_rfm`, and optionally `analytics.vw_product_interest` or `analytics.fact_product_views`. Do not import staging. Follow `powerbi/model_documentation.md` for relationships, the four report pages, and `powerbi/measures.dax` for measures. Compare unsliced cards to SQL validation and apply date, region and shipping-mode slicers to confirm denominators. The product interest chart has its own log window and does not measure conversion. Save the `.pbix` locally after checking model relationships and visuals. No `.pbix` has been created in this workspace.
