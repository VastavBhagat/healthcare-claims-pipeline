# Architecture Overview

## Data Flow

```
data.cms.gov (public API)
        |
        | HTTP - paginated JSON
        v
ingestion/download_cms.py        <- validates row count + checksum
        |
        | Azure Blob SDK
        v
ADLS Gen2  /raw                  <- raw JSONL files
        |
        | ADF pipeline (PL_CMS_To_Blob)
        v
Snowflake RAW schema             <- raw tables with audit columns
        |
        | dbt staging models (views)
        v
Snowflake STAGING schema         <- cleaned, typed, renamed
        |
        | dbt intermediate models (tables)
        v
Snowflake INTERMEDIATE schema    <- aggregations by provider, procedure
        |
        | dbt mart models (tables)
        v
Snowflake MARTS schema           <- fct_claims, dim_provider, dim_procedure, dim_region
        |
        | DirectQuery / scheduled import
        v
Power BI dashboard
```

## Orchestration (Airflow DAG chain)

```
dag_ingest_claims
  -> trigger ADF pipeline
  -> poll for completion
  -> validate blob landing
        |
        v (ExternalTaskSensor)
dag_transform_claims
  -> dbt run staging
  -> dbt run intermediate
  -> dbt run marts
  -> dbt snapshot (SCD Type 2)
        |
        v (ExternalTaskSensor)
dag_quality_checks
  -> dbt test --store-failures
  -> write audit log to Snowflake
        |
        v (on_failure_callback)
dag_notify
  -> send email alert
```

## Snowflake Schema Layout

```
HEALTHCARE_DB
  |-- RAW
  |     |-- cms_claims
  |     |-- cms_providers
  |     |-- cms_procedures
  |-- STAGING
  |     |-- stg_cms_claims       (view)
  |     |-- stg_cms_providers    (view)
  |     |-- stg_cms_procedures   (view)
  |-- INTERMEDIATE
  |     |-- int_claims_by_provider    (table)
  |     |-- int_claims_by_procedure   (table)
  |-- MARTS
  |     |-- fct_claims           (table)
  |     |-- dim_provider         (table)
  |     |-- dim_procedure        (table)
  |     |-- dim_region           (table)
  |-- SNAPSHOTS
  |     |-- provider_snapshot    (SCD Type 2)
  |-- AUDIT
        |-- quality_results
```

## Infrastructure (Terraform)

All Azure and Snowflake resources are provisioned via Terraform in `infra/terraform/`.
Dev and prod environments are separated using Terraform workspaces with `var.environment`.

Azure resources: Resource Group, Storage Account (ADLS Gen2 with HNS), three containers (raw/staging/archive), Azure Data Factory with system-assigned managed identity.

Snowflake resources: database per environment, six schemas, X-Small warehouse (dev) / Small warehouse (prod) with 60-second auto-suspend.
