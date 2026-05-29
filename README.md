# Healthcare Claims Pipeline

[![CI](https://github.com/VastavBhagat/healthcare-claims-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/VastavBhagat/healthcare-claims-pipeline/actions/workflows/ci.yml)

A data engineering pipeline built on the CMS Medicare public dataset. It covers the full stack: Python ingestion scripts, Azure Blob Storage, ADF, Snowflake, dbt transformations with SCD Type 2, Airflow orchestration, and a Power BI dashboard. Infrastructure is provisioned with Terraform.

The main focus is on things that tend to get skipped in simpler portfolio projects - audit logging, anomaly detection on billing patterns, SCD Type 2 for provider history, and a proper CI/CD workflow that separates linting, testing, and deployment.

---

## Stack

| Layer | Tool |
|---|---|
| Source | CMS Medicare Provider Utilization data (data.cms.gov public API) |
| Ingestion | Python scripts + Azure Data Factory |
| Storage | Azure Data Lake Storage Gen2 (raw / staging / archive) |
| Warehouse | Snowflake (RAW / STAGING / INTERMEDIATE / MARTS / SNAPSHOTS) |
| Transformation | dbt Cloud |
| Orchestration | Apache Airflow (Docker Compose locally, or Astronomer) |
| Infrastructure | Terraform (Azure + Snowflake) |
| Dashboard | Power BI |
| CI/CD | GitHub Actions |

---

## Architecture

```
data.cms.gov API
        |
        |  paginated JSON
        v
ingestion/download_cms.py        validates row count + checksum
        |
        v
ADLS Gen2  /raw
        |
        |  ADF pipeline
        v
Snowflake RAW schema
        |
        |  dbt staging (views)
        v
STAGING schema                   cleaned, typed, renamed
        |
        |  dbt intermediate (tables)
        v
INTERMEDIATE schema              provider + procedure aggregations
        |
        |  dbt marts (tables)
        v
MARTS schema                     fct_claims, dim_provider, dim_procedure, dim_region
        |
        v
Power BI dashboard
```

Airflow chains the four stages as dependent DAGs:
`dag_ingest_claims -> dag_transform_claims -> dag_quality_checks -> dag_notify (on failure)`

---

## dbt Models

```
RAW (sources)
  |-- cms_claims
  |-- cms_providers
  |-- cms_procedures
        |
        | staging (views)
        v
  stg_cms_claims
  stg_cms_providers
  stg_cms_procedures
        |
        | intermediate (tables)
        v
  int_claims_by_provider      aggregates per NPI: total payment, stddev
  int_claims_by_procedure     aggregates per HCPCS code
        |
        | marts (tables)
        v
  fct_claims                  one row per claim + is_payment_anomaly flag (3-sigma)
  dim_provider                NPI + billing stats + SCD Type 2 via snapshot
  dim_procedure               HCPCS codes + national avg payment
  dim_region                  state-level claim volume and cost
```

### Anomaly detection

`fct_claims` flags any claim where `payment_amount` is more than 3 standard deviations above the provider's own historical average. The stddev is pulled from `int_claims_by_provider`. There's also a custom dbt test that surfaces these in CI so anomaly counts don't silently grow between runs.

### SCD Type 2

Provider details (name, address, specialty) are tracked with `dbt snapshot`. Any change to a provider's attributes creates a new row with `dbt_valid_from` / `dbt_valid_to`, so historical claims can be joined back to provider data as it was at the time of service.

---

## Data Quality Tests

dbt tests cover all mart models. Custom tests are in `dbt_project/tests/`:

| Test | What it checks |
|---|---|
| `unique`, `not_null` on all primary keys | Basic integrity across all mart tables |
| `relationships` on `fct_claims.provider_npi` | Every claim has a matching provider |
| `relationships` on `fct_claims.procedure_code` | Every claim has a matching procedure |
| `test_anomaly_detect_claims.sql` | Returns claims with payment z-score > 3 |
| `test_duplicate_claims.sql` | Returns same provider + procedure within a 30-day window |

Running `dbt test --store-failures` writes failure rows back to Snowflake for investigation.

---

## Airflow DAGs

| DAG | Schedule | What it does |
|---|---|---|
| `dag_ingest_claims` | Daily 6am | Triggers ADF pipeline, polls for completion, validates blob landing |
| `dag_transform_claims` | Daily 7am | Runs dbt staging -> intermediate -> marts -> snapshot in order |
| `dag_quality_checks` | Daily 8am | Runs dbt tests, writes summary to AUDIT.quality_results |
| `dag_notify` | On failure | Sends email alert on any upstream DAG failure |

DAGs use `ExternalTaskSensor` to enforce the dependency chain. Airflow connection IDs and variables (`adf_resource_group`, `alert_email`, etc.) are configured via the Airflow UI or environment variables.

---

## Infrastructure

Terraform in `infra/terraform/` provisions everything:

- Azure Resource Group, ADLS Gen2 storage account with three containers, ADF instance
- ADF managed identity granted `Storage Blob Data Contributor` on the storage account
- Snowflake warehouse (X-Small in dev, Small in prod) with 60-second auto-suspend
- Snowflake database with all six schemas

Dev and prod are separated by `var.environment`. The Terraform state lives in a separate Azure storage account.

CI plan runs on every PR to `infra/terraform/`. Apply runs on merge to main.

---

## CI/CD

Three separate GitHub Actions workflows:

| Workflow | Trigger | What runs |
|---|---|---|
| `ci.yml` | PR to main | black, flake8, sqlfluff, pytest, dbt compile |
| `deploy.yml` | Push to main | dbt run + test on dev Snowflake; on tag release, deploy to prod |
| `terraform.yml` | PR or push touching `infra/` | terraform plan (PR) or terraform apply (push) |

All Snowflake and Azure credentials are stored as GitHub repository secrets.

---

## Project Structure

```
healthcare-claims-pipeline/
+-- ingestion/
|   +-- download_cms.py          fetches CMS data page by page, validates checksum
|   +-- upload_to_blob.py        uploads to raw / staging / archive zone
|   +-- utils.py                 logging, checksum, retry decorator
+-- dbt_project/
|   +-- models/
|   |   +-- staging/             sources.yml + 3 staging views
|   |   +-- intermediate/        2 aggregation tables
|   |   +-- marts/               4 analytical tables + schema.yml tests
|   +-- snapshots/               provider_snapshot.sql (SCD Type 2)
|   +-- tests/                   anomaly detection + duplicate claims custom tests
|   +-- dbt_project.yml
+-- airflow/
|   +-- dags/                    4 DAG files
|   +-- plugins/
+-- infra/terraform/             main.tf, variables.tf, outputs.tf, providers.tf
+-- tests/                       pytest unit tests for ingestion scripts
+-- dashboard/                   Power BI screenshots and connection notes
+-- docs/
|   +-- DESIGN_DECISIONS.md      why SCD2, why Snowflake schema layout, why 3-sigma
|   +-- architecture.md          full data flow and schema diagram
+-- .env.example
+-- .pre-commit-config.yaml      black, flake8, sqlfluff hooks
+-- docker-compose.yml           Airflow local setup
+-- requirements.txt
+-- README.md
```

---

## Running Locally

Copy `.env.example` to `.env` and fill in your credentials.

**Ingestion scripts:**
```bash
pip install -r requirements.txt
python ingestion/download_cms.py
python ingestion/upload_to_blob.py data/raw/cms_claims_raw.jsonl raw
```

**Airflow (Docker Compose):**
```bash
docker-compose up airflow-init
docker-compose up
```
Access the Airflow UI at `http://localhost:8080` (admin / admin).

**dbt:**
```bash
cd dbt_project
pip install dbt-snowflake
dbt debug
dbt run
dbt test
dbt snapshot
```

**Tests:**
```bash
pytest tests/ -v
```

**Terraform:**
```bash
cd infra/terraform
terraform init
terraform plan -var="environment=dev" -var="snowflake_account=..." ...
terraform apply
```

---

Dataset: [CMS Medicare Provider Utilization and Payment Data](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service)
