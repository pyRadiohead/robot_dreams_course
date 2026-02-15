"""
Airflow DAG: Enrich User Profiles Pipeline
Schedule: Manual trigger (no schedule)
Tasks: silver → gold (RDS PostgreSQL)
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
    'enrich_user_profiles',
    default_args=default_args,
    description='Enrich user profiles and write to RDS PostgreSQL gold layer',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['enrichment', 'gold', 'manual', 'rds']
) as dag:

    # Task: Enrich and write to Gold layer (RDS)
    enrich_to_gold = GlueJobOperator(
        task_id='enrich_to_gold',
        job_name='enrich_user_profiles',
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    enrich_to_gold

