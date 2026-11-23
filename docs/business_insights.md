# Findings and actions to evaluate

| Observation | Evidence | Investigation | Success measure |
| --- | --- | --- | --- |
| Delivery promises are frequently missed in the reporting scope | 16,633 / 28,965 eligible finished orders, 57.42% | Audit timestamp and promise-day definitions by shipping mode and lane | Late order rate, sample size and actual minus scheduled days |
| First Class is uniformly late in the observed completed subset | 4,497 / 4,497 orders | Check whether scheduled day values are a service definition artifact | Verified SLA compliance by lane after audit |
| Delayed orders contain substantial recorded sales | 8,255,939.77 in net order sales on late orders | Prioritize service monitoring where exposure and volumes are high | Late-order count and rate; no unmeasured lost-sales claim |
| Completed-order customers include repeat buyers | 7,488 / 14,543 (51.49%) have >= 2 finished orders | Design a retention experiment targeting suitable segments | Subsequent purchase rate, profit after offer cost |
| Access-log activity can be compared by product name | 469,977 events across 76 logged names; 72 catalog matches | Review high-activity product pages and compare sales over the same date window | Page events and separately recorded item sales; no visitor conversion claim |

None of the actions has been implemented by DataCo. Mode or region differences may reflect promise differences and customer mix. Collect freight costs, carrier and route information, customer feedback and return/refund data before forecasting savings. For an illustrative operational scenario only, converting 100 otherwise eligible late orders to on-time would reduce the rate by `100 / 28,965 = 0.345` percentage points at a fixed denominator; it does not establish a feasible intervention or financial impact.
