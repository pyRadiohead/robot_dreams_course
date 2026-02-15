"""
Airflow DAG: Process User Profiles Pipeline
Schedule: Manual trigger (no schedule)
Tasks: raw → silver
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
    'process_user_profiles',
    default_args=default_args,
    description='Process user profiles data from raw to silver layer',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['user_profiles', 'etl', 'manual']
) as dag:

    # Task: Raw to Silver (direct, no bronze layer)
    user_profiles_raw_to_silver = GlueJobOperator(
        task_id='user_profiles_raw_to_silver',
        job_name='process_user_profiles_raw_to_silver',
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    user_profiles_raw_to_silver

