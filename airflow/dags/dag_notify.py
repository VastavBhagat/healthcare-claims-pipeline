"""
Listens for failures in upstream DAGs and sends an alert email.
Triggered by task failure callbacks rather than on a schedule.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.utils.email import send_email


ALERT_EMAIL = Variable.get("alert_email", default_var="")


def on_failure_callback(context: dict) -> None:
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    run_id = context["run_id"]
    log_url = context["task_instance"].log_url

    subject = f"[Airflow] Pipeline failure: {dag_id}.{task_id}"
    body = f"""
    <b>DAG:</b> {dag_id}<br>
    <b>Task:</b> {task_id}<br>
    <b>Run ID:</b> {run_id}<br>
    <b>Log:</b> <a href="{log_url}">{log_url}</a>
    """
    send_email(to=ALERT_EMAIL, subject=subject, html_content=body)


@dag(
    dag_id="dag_notify",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["notify"],
    on_failure_callback=on_failure_callback,
)
def notify():

    @task
    def placeholder() -> None:
        pass

    placeholder()


notify()
