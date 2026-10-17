from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ecommerce_etl_pipeline',
    default_args=default_args,
    description='Bronze -> Silver -> Gold ETL Pipeline',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    # Note: In a real Docker setup, we would run these via DockerOperator or SSH,
    # but for a local simulation, we will simulate the bash commands.
    
    load_bronze = BashOperator(
        task_id='load_to_postgres_bronze',
        bash_command='echo "Simulating: python /opt/airflow/scripts/01_load_to_postgres.py"',
    )

    clean_spark_silver = BashOperator(
        task_id='spark_clean_to_silver',
        bash_command='echo "Simulating: python /opt/airflow/scripts/02_spark_clean_to_silver.py"',
    )

    build_gold_duckdb = BashOperator(
        task_id='build_gold_aggregations',
        bash_command='echo "Simulating: python /opt/airflow/scripts/03_build_gold.py"',
    )

    load_bronze >> clean_spark_silver >> build_gold_duckdb