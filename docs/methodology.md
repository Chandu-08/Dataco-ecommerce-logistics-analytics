# Steps and checks

1. Inspect `data/raw/DescriptionDataCoSupplyChain.csv`. Import the order CSV and access logs into separate SQL Server staging tables with `import_raw_sql_server.py`, preserving the source text privately.
2. Run SQL cleaning and SQL transformations. `clean.order_items` uses `TRY_CONVERT`; validation fails on bad keys, dates, quantities or financial identities. SQL facts preserve item and order grains and reconcile net sales. `clean.access_events` parses dates, and `fact_product_views` groups events by day and normalized product name while excluding IP-like values.
3. Select COMPLETE/CLOSED for the primary reporting scope. Inspect alternative status definitions separately before making business decisions.
4. Read validated SQL facts and aggregated product events into Python with `after_sql.py`. Group eligible orders by stable customer ID. Use day-after-last-purchase snapshot, transparent percentile thresholds and distinct-order frequency, then write RFM segments back to SQL Server. Compare product page events with same-window sales by normalized name; do not infer visitor-to-purchase conversion.
5. Count one shipping outcome per eligible order. Compare scheduled and real shipping days; cross-check `Delivery Status`. Use Wilson binomial intervals as descriptive uncertainty summaries; orders may be dependent, so these intervals are not experimental effect estimates.
6. Build category, market, discount, cohort and mode aggregates in Python. Connect Power BI to SQL analytics tables and validate its cards against SQL and Python. Review outliers, month coverage and sample sizes.

The source's First Class rate (100% under the recorded definition) suggests shipping-mode promise structure strongly shapes the result. Changing a shipping mode cannot be recommended on this rate alone; compare route and service commitments and obtain cost data.
