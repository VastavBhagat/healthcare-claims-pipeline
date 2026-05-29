# Dashboard

Power BI dashboard connecting to `HEALTHCARE_DB.MARTS` via scheduled import.

## Report Pages

| Page | Description |
|---|---|
| Executive Summary | Total claims, total cost, avg cost per claim with state filter |
| State Comparison | Side-by-side claim volume and payment across regions |
| Provider Drill-down | Top providers by payment amount, anomaly flags highlighted |
| Processing Bottlenecks | Claim count bucketed by processing time |
| Data Quality Monitor | dbt test pass/fail rates over time, anomaly count trend |

## Connection Setup

1. Open Power BI Desktop
2. Get Data -> Snowflake
3. Server: `<your-account>.snowflakecomputing.com`
4. Warehouse: `CLAIMS_WH`
5. Database: `HEALTHCARE_DB`
6. Schema: `MARTS`
7. Import mode for scheduled refresh, DirectQuery for live exploration

## Screenshots

Add dashboard screenshots here once the Power BI report is built.
