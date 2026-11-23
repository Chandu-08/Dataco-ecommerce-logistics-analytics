# Verified source fields and grain

The 53-column Kaggle CSV has one row per `Order Item Id` (180,519 unique IDs). `Order Id` identifies 65,752 orders; every tested order-level field is constant within its order. `Customer Id` equals `Order Customer Id` in all rows. Both CSVs use Latin-1 decoding. The companion description file describes `Order Item Total` as total amount after discount and `Sales` as product/item sales. Source arithmetic verifies `Sales - Order Item Discount = Order Item Total`, and `Order Item Quantity × Order Item Product Price = Sales`, each to two cents for all rows.

| Source | Use | Grain |
| --- | --- | --- |
| Order Item Id | primary item key | item |
| Order Id | primary order key, grouped from items | order |
| Order Customer Id | customer key | order |
| Sales / Order Item Discount / Order Item Total | gross / discount / net sales | item |
| Order Profit Per Order / Benefit per order | identical recorded amounts across all item rows; select first as recorded profit | item in source, despite label |
| order date (DateOrders) | purchase proxy | order |
| Days for shipping (real) / Days for shipment (scheduled) | shipping day comparison | order |
| Delivery Status / Late_delivery_risk | outcome descriptors; never explanatory variables for late outcome | order |
| Order Status | completion reporting filter | order |
| Shipping Mode / Market / Order Region | descriptive breakdown | order |

PII including `Customer Password`, email, names and street is excluded from analytical facts. Dates are parsed in month/day/year hour:minute format. Negative profits are retained. Statuses other than COMPLETE/CLOSED are retained in local facts but excluded from the primary financial KPI. CANCELED/SUSPECTED_FRAUD are shipping canceled in the observed data.

## Access logs

`tokenized_access_logs.csv` has 469,977 records and eight source fields: `Product`, `Category`, `Date`, `Month`, `Hour`, `Department`, `ip`, and `url`. One record represents an access log event, **not** a distinct visitor or purchase. The SQL clean layer uses `Product`, `Date`, `Category`, and `Department`; the analytics layer keeps only date, normalized product name and event count. IP-like values and URLs stay in restricted staging. The log has no order or customer key. Product names can be matched descriptively after trimming and lowercasing; 72 of 76 logged names match the order catalog, but this does not establish that a logged event led to a purchase.
