from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "data_engineer",
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "supermarket_sales_pipeline",
    default_args=default_args,
    description="Конвейер: Инжест -> dbt Трансформация -> ML Прогноз",
    schedule_interval="@daily",
    catchup=False,
    tags=["supermarket", "dwh", "dbt", "ml"],
) as dag:

    run_generator = BashOperator(
        task_id="generate_and_load_sales",
        bash_command="python3 /opt/airflow/scripts/generate_sales.py 1",
    )

    run_dbt = BashOperator(
        task_id="run_dbt_transformations",
        bash_command="cd /opt/airflow/dbt && dbt run --project-dir . --profiles-dir .",
    )

    run_forecast = BashOperator(
        task_id="run_ml_forecasting",
        bash_command="python3 /opt/airflow/scripts/predict_sales.py",
    )

    run_generator >> run_dbt >> run_forecast
