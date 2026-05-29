"""
Runs dbt models in dependency order after ingestion completes.
Uses the Bash operator to call dbt CLI commands against the Snowflake target.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor


DBT_DIR = "/opt/airflow/dbt_project"

default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
    "email_on_failure": True,
}


@dag(
    dag_id="dag_transform_claims",
    schedule_interval="0 7 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["dbt", "transform"],
)
def transform_claims():

    wait_for_ingestion = ExternalTaskSensor(
        task_id="wait_for_ingestion",
        external_dag_id="dag_ingest_claims",
        external_task_id=None,
        timeout=3600,
        poke_interval=60,
    )

    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"cd {DBT_DIR} && dbt run --select staging",
    )

    dbt_run_intermediate = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command=f"cd {DBT_DIR} && dbt run --select intermediate",
    )

    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"cd {DBT_DIR} && dbt run --select marts",
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"cd {DBT_DIR} && dbt snapshot",
    )

    wait_for_ingestion >> dbt_run_staging >> dbt_run_intermediate >> dbt_run_marts >> dbt_snapshot


transform_claims()
