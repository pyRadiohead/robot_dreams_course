"""
Airflow DAG: Process Customers Pipeline
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
    'process_customers',
    default_args=default_args,
    description='Process customers data from raw to silver layer',
    schedule_interval='@daily',
    catchup=False,
    tags=['customers', 'etl', 'daily']
) as dag:

    # Task 1: Raw to Bronze
    customers_raw_to_bronze = GlueJobOperator(
        task_id='customers_raw_to_bronze',
        job_name='process_customers_raw_to_bronze',
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    # Task 2: Bronze to Silver
    customers_bronze_to_silver = GlueJobOperator(
        task_id='customers_bronze_to_silver',
        job_name='process_customers_bronze_to_silver',
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    # Define task dependencies
    customers_raw_to_bronze >> customers_bronze_to_silver

