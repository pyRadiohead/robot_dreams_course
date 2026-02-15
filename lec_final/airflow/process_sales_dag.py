"""
Airflow DAG: Process Sales Pipeline
Schedule: Daily (@daily)
Tasks: raw → bronze → silver
"""

from airflow import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from datetime import datetime, timedelta

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
with DAG(
    'process_sales',
    default_args=default_args,
    description='Process sales data from raw to silver layer',
    schedule_interval='@daily',
    catchup=False,
    tags=['sales', 'etl', 'daily']
) as dag:

    # Task 1: Raw to Bronze
    sales_raw_to_bronze = GlueJobOperator(
        task_id='sales_raw_to_bronze',
        job_name='process_sales_raw_to_bronze',
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    # Task 2: Bronze to Silver
    sales_bronze_to_silver = GlueJobOperator(
        task_id='sales_bronze_to_silver',
        job_name='process_sales_bronze_to_silver',
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    # Define task dependencies
    sales_raw_to_bronze >> sales_bronze_to_silver

