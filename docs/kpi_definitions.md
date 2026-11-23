# Metric contracts

| KPI | Numerator / denominator | Eligible population |
| --- | --- | --- |
| Net sales | `SUM(Order Item Total)` | item rows in COMPLETE/CLOSED orders |
| Recorded profit | `SUM(Order Profit Per Order)` | same eligible item rows; verified distinct item values |
| Margin | profit / net sales | same population |
| Orders | `COUNT(DISTINCT Order Id)` | COMPLETE/CLOSED |
| Customers | `COUNT(DISTINCT Order Customer Id)` | COMPLETE/CLOSED |
| AOV | eligible order net sales / eligible orders | COMPLETE/CLOSED |
| Repeat customers | customers with >= 2 distinct eligible order IDs | COMPLETE/CLOSED |
| Late order rate | eligible orders with real shipping days > scheduled days / eligible shipping orders | COMPLETE/CLOSED with valid nonnegative shipping days and noncanceled delivery |
| Positive delay | `AVG(real days - scheduled days)` | late eligible orders |
| Late sales exposure | net order sales summed once on late eligible orders | descriptive exposure, not lost sales |

RFM snapshot: day after last eligible order date (2018-02-01). Monetary high value is >= 75th percentile, recent is <= median recency, inactive is >= 75th percentile recency; repeat means >= 2 eligible orders. Segments are ordered by the first matching condition in code, and these thresholds describe the observed sample. Cohort retention compares observed distinct customers who order in month `t` with cohort size at `t=0`; incomplete follow-up makes later cohorts incomparable at longer horizons.
