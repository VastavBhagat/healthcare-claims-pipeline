# Design Decisions

Notes on the key architectural choices made in this project and the reasoning behind them.

---

## Why SCD Type 2 for providers

Provider details like name, address, and specialty change over time. If you only keep the current state, you lose the ability to answer questions like "what was this provider's specialty when they submitted this claim?" or "when did this provider change their address?"

dbt snapshots handle this cleanly. The `provider_snapshot` tracks changes with `dbt_valid_from` and `dbt_valid_to` columns, so historical claims can always be joined back to the provider record as it was at the time of service.

The alternative (SCD Type 1, just overwrite) was rejected because it would silently corrupt historical analysis.

---

## Why separate Snowflake schemas per layer (RAW / STAGING / INTERMEDIATE / MARTS)

Four-layer separation follows the medallion principle but maps it to Snowflake schemas rather than storage zones:

- **RAW** - untouched data as it arrived from ADF. Preserved for replay.
- **STAGING** - cleaned and typed, no business logic, materialised as views so there is no storage cost and queries always reflect the latest raw data.
- **INTERMEDIATE** - aggregations and joins that are reused by multiple mart models. Materialised as tables because the aggregations are expensive and referenced repeatedly.
- **MARTS** - the analytical layer that Power BI connects to. Physical tables, optimised for BI query patterns.

Keeping these in separate schemas also makes Snowflake RBAC simpler. Analysts only need SELECT on MARTS. Engineers need CREATE on all four.

---

## Why Snowflake schema-per-region is not implemented (yet)

The original design considered separate schemas per US state (CLAIMS_CA, CLAIMS_TX, etc.) for data isolation and row-level filtering. This was deprioritised because:

1. The CMS dataset is federal-level data - state filtering is a column filter, not a structural concern.
2. Schema-per-region would multiply the number of dbt models and make CI significantly more complex.

If this were a multi-tenant product with strict data isolation requirements (e.g. each state health department can only see their own data), the schema-per-region approach would be appropriate. For analytics reporting purposes, a `provider_state` column with Snowflake row-level security policies is simpler and easier to maintain.

---

## Why anomaly detection uses 3 standard deviations

The 3-sigma threshold is a standard statistical baseline for outlier flagging. It catches roughly the top 0.3% of claims by payment deviation from a provider's own historical average - unusual enough to be worth reviewing without generating too many false positives.

The flag is computed in `fct_claims.sql` using pre-aggregated stats from `int_claims_by_provider.sql`, so the stddev is calculated across the provider's full history rather than per-run. There is also a custom dbt test (`test_anomaly_detect_claims.sql`) that surfaces the same logic as a test so anomalies are visible in CI.

This is a flag, not a filter. Anomalous claims are still included in all aggregations; the flag just makes them easy to surface in the Power BI dashboard.

---

## Why Airflow over GitHub Actions for orchestration

GitHub Actions is used for CI/CD (code validation on push). Airflow handles operational scheduling because:

- Airflow supports DAG dependencies, SLA monitoring, and retry policies that are awkward to model in GitHub Actions.
- The `ExternalTaskSensor` between DAGs means the transform step will not start until ingestion is confirmed complete.
- Airflow's UI gives visibility into historical runs, task logs, and failure state that GitHub Actions does not.

For a simpler project, GitHub Actions would be sufficient. The added Airflow complexity is justified here by the multi-step dependency chain and the need for operational visibility.

---

## Why pytest over just dbt tests for Python validation

dbt tests cover SQL models. Python ingestion scripts (download, upload, checksum validation) are tested separately with pytest because:

- The ingestion layer has real failure modes: API timeouts, partial downloads, incorrect SAS token scopes.
- Mocking Azure and CMS API calls in pytest is straightforward and runs without any cloud credentials.
- Keeping ingestion tests in Python means they run in the CI linting job without needing Snowflake credentials.
