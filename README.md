# E-Commerce Revenue, Customer Segmentation & Logistics Performance

An end-to-end DataCo Smart Supply Chain portfolio analysis for a decision analytics interview. The primary workflow is **SQL Server import and transformations → Python customer and logistics analytics → Power BI reporting**. The project reconciles item-level finance with order-level delivery, segments finished-order customers, and provides a local four-page report and a Power BI implementation guide.

**Dataset:** DataCo Smart Supply Chain for Big Data Analysis, Fabian Constante, Fernando Silva and António Pereira, Mendeley Data v5, DOI [10.17632/8gx2fvg2k6.5](https://data.mendeley.com/datasets/8gx2fvg2k6/5), CC BY 4.0. This project was rerun against the user's uploaded `DataCoSupplyChainDataset.csv`, `DescriptionDataCoSupplyChain.csv` and `tokenized_access_logs.csv`. The first two are byte-for-byte identical to the [Kaggle copy](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) originally analyzed. The source contains orders dated 2015–2018 and access events dated September 2017–January 2018. Currency is not confirmed; amounts are shown without a currency symbol.

## Observed results and definitions

| Metric | Verified result | Definition |
| --- | ---: | --- |
| Raw item rows | 180,519 | Original CSV records |
| Distinct orders | 65,752 | Distinct `Order Id` across all statuses |
| Finished-order net sales | 14,476,738.58 | Sum of `Order Item Total` for COMPLETE/CLOSED |
| Finished-order recorded profit | 1,779,716.84 | Sum of item-level `Order Profit Per Order` for COMPLETE/CLOSED |
| Finished orders | 28,965 | Distinct orders in COMPLETE/CLOSED |
| Eligible late orders | 16,633 of 28,965 (57.42%) | Completed, valid shipping data; actual days > scheduled days |
| Sales associated with late orders | 8,255,939.77 | Net sales booked on those orders; **not lost sales** |
| Finished-order customers | 14,543 | Distinct order customer IDs in eligible orders |
| Product page events | 469,977 | Log events; not unique customers or purchases |
| Logged product names matched to catalog | 72 of 76 | Exact match after trimming and lowercasing product names |

Financial status policy is a transparent **reporting assumption**, not proof of payment settlement. The original dataset contains 20,652 distinct customers across all statuses. The `Order Profit Per Order` field is repeated per item as a separate item-level value; source description wording is ambiguous, so treat this as recorded profit rather than verified accounting profit. Every First Class finished order is flagged late in this dataset; inspect promise-day semantics before recommending operational changes.

## Reproduce

1. Install Python 3.10+ and `pip install -r requirements.txt`; install `pyodbc` and a compatible Microsoft SQL Server ODBC driver. Install or connect to SQL Server and open SSMS.
2. Put the three uploaded CSVs (`DataCoSupplyChainDataset.csv`, `DescriptionDataCoSupplyChain.csv`, `tokenized_access_logs.csv`) in `data/raw/`. Keep raw files private.
3. In SSMS run `sql/01_database_setup.sql`. Set the local `DATACO_ODBC_CONNECTION` environment variable. Import orders with `python python/import_raw_sql_server.py --dataset orders`, and logs with `python python/import_raw_sql_server.py --dataset logs`. In SSMS run `sql/02_data_cleaning.sql`, `sql/03_dimensional_model.sql`, and `sql/08_clickstream.sql`.
4. Run `python python/after_sql.py`, `python python/analyze.py`, `python python/statistics.py` and `python python/render_report.py`. Python reads the SQL facts and writes RFM segments back to SQL Server. Open `dashboards/four_page_report.html` to inspect the generated report.
5. Run SQL analysis/validation scripts `sql/04_revenue_analysis.sql` through `sql/07_data_validation.sql`; compare values with `docs/kpi_results.json`.
6. In Power BI Desktop, connect to the SQL Server analytics tables following `powerbi/model_documentation.md`; add measures from `powerbi/measures.dax` and validate cards. No `.pbix` is included because Power BI Desktop is unavailable here.

The detailed commands and expected validation counts are in [`docs/SQL_TO_PYTHON_TO_POWERBI.md`](docs/SQL_TO_PYTHON_TO_POWERBI.md). This environment lacks SQL Server and its ODBC driver, so the new SQL path requires execution on a connected machine. The previous Python-only source validation was executed on the actual Kaggle CSV; the recorded figures above are from that check, not an unverified SQL run.

## Workflow

`Original orders + access logs` → `SQL Server raw staging` → `SQL cleaning, item/order facts + product event aggregates` → `Python reads SQL facts and builds RFM/cohorts/product interest` → `Python segments written to SQL` → `Power BI reads SQL analytics tables`.

SQL shows CTEs, joins, conditional KPIs, window functions, date analysis and reconciliation. Python performs source checks, order-level rollup, descriptive RFM segmentation, monthly retention and Wilson intervals by shipping mode. `docs/` explains the business question, KPI policy, observed results, constraints and resume wording.

**Data protection:** Source records contain email, names, password-like and location fields; logs include IP-like fields. SQL staging contains the original sensitive columns; restrict database access and do not publish a staging backup. Clean/analytics exclude the personal/IP fields. Original CSVs and customer/order-level exports are excluded from the distributable ZIP.
