"""
Runs dbt tests and writes results to a quality_results audit table in Snowflake.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor


DBT_DIR = "/opt/airflow/dbt_project"

default_args = {
    "owner": "data-engineering",
    "retries": 0,
    "email_on_failure": True,
}


@dag(
    dag_id="dag_quality_checks",
    schedule_interval="0 8 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["quality", "dbt"],
)
def quality_checks():

    wait_for_transform = ExternalTaskSensor(
        task_id="wait_for_transform",
        external_dag_id="dag_transform_claims",
        external_task_id=None,
        timeout=3600,
        poke_interval=60,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test --store-failures",
    )

    @task
    def write_audit_log(run_date: str = None) -> None:
        """Writes a summary of test results to HEALTHCARE_DB.AUDIT.quality_results."""
        import snowflake.connector
        import os

        conn = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            database="HEALTHCARE_DB",
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "CLAIMS_WH"),
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO AUDIT.quality_results (run_date, source, status, notes, created_at)
            SELECT
                current_date(),
                'dbt_test',
                'completed',
                'Daily dbt test run',
                current_timestamp()
        """)
        conn.close()

    wait_for_transform >> dbt_test >> write_audit_log()


quality_checks()
