# Business requirements

| Question | KPI | Decision enabled | Main limit |
| --- | --- | --- | --- |
| Where do finished-order sales and profit come from? | Item net sales, profit and margin by category, market and month | Prioritize margin review | Status is not verified settlement; cost model unknown |
| Which customer groups merit attention? | Distinct completed orders, recency, frequency and observed spending | Design a retention experiment | Observation starts 2015 and ends 2018; inactivity is not churn |
| Which deliveries breach schedule? | Late completed orders / eligible completed orders, by mode and region | Audit promises and processes | Duration and status describe outcomes, not root cause |
| Where do high value and delivery exposure overlap? | Order sales associated with delay, segment x delay rate | Choose investigation cohorts | Exposure is not revenue loss |

Hypotheses to test descriptively: discount bands may differ in recorded margin; service compliance may differ by shipping mode; high-value repeat customers may experience delays. Differences are associations. Required data: source identifiers, item financial fields, dates, order status, shipping durations, market and mode. Missing actual carrier cost, freight expense, returns, recovery actions, customer feedback and randomized treatment prevent causal savings claims.

Access logs add a separate product-interest question: which product pages generated the most recorded events during the log window, and what recorded sales did those product names have during the same window? There is no shared customer, visit/session or order ID, so this cannot calculate a conversion funnel or attribute a sale to a visit.
