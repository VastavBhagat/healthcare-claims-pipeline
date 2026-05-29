"""
Triggers the ADF ingestion pipeline, polls until completion,
then validates the output file landed in Blob Storage.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.microsoft.azure.hooks.data_factory import AzureDataFactoryHook


ADF_CONN_ID = "azure_data_factory_default"
RESOURCE_GROUP = Variable.get("adf_resource_group", default_var="rg-healthcare")
FACTORY_NAME = Variable.get("adf_factory_name", default_var="adf-healthcare")
PIPELINE_NAME = "PL_CMS_To_Blob"


default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": Variable.get("alert_email", default_var=""),
}


@dag(
    dag_id="dag_ingest_claims",
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "adf"],
)
def ingest_claims():

    @task
    def trigger_adf_pipeline() -> str:
        hook = AzureDataFactoryHook(azure_data_factory_conn_id=ADF_CONN_ID)
        run_id = hook.run_pipeline(
            pipeline_name=PIPELINE_NAME,
            resource_group_name=RESOURCE_GROUP,
            factory_name=FACTORY_NAME,
        )
        return run_id

    @task
    def wait_for_completion(run_id: str) -> dict:
        hook = AzureDataFactoryHook(azure_data_factory_conn_id=ADF_CONN_ID)
        result = hook.wait_for_pipeline_run(
            run_id=run_id,
            resource_group_name=RESOURCE_GROUP,
            factory_name=FACTORY_NAME,
            check_interval=30,
            timeout=3600,
        )
        if result["status"] != "Succeeded":
            raise RuntimeError(f"ADF pipeline failed with status: {result['status']}")
        return result

    @task
    def validate_blob_landing(run_result: dict) -> None:
        from azure.storage.blob import BlobServiceClient
        import os

        conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        container = os.environ.get("AZURE_CONTAINER_RAW", "raw")
        client = BlobServiceClient.from_connection_string(conn_str)

        blobs = list(client.get_container_client(container).list_blobs())
        if not blobs:
            raise RuntimeError(f"No files found in '{container}' container after ADF run")

    run_id = trigger_adf_pipeline()
    result = wait_for_completion(run_id)
    validate_blob_landing(result)


ingest_claims()
