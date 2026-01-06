from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
import os

# custom operator
from dbt_operator import DbtOperator

# constants
PROJECT_DIR = os.getenv('AIRFLOW_HOME') + "/dags/dbt/homework"
PROFILE = 'homework'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email': ['ethingwillbefine@gmail.com'],
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}
with DAG(
    dag_id='process_iris',
    default_args=default_args,
    description='Process Iris dataset with dbt and ML',
    schedule_interval='0 22 * * *',
    start_date=datetime(2025, 4, 22),
    end_date=datetime(2025, 4, 25),
    catchup=True,
    tags=['homework', 'ml', 'dbt'],
) as dag:
    dbt_transform = DbtOperator(
        task_id='dbt_transform_iris',
        command='run',
        profile=PROFILE,
        project_dir=PROJECT_DIR,
        models=['+iris_processed'],
        vars={
            'execution_date': '{{ ds }}',
        },
    )
    #process_iris model
    from python_scripts.train_model import process_iris_data

    #inference model
    from python_scripts.inference import run_inference

    train_model = PythonOperator(
        task_id='train_ml_model',
        python_callable=process_iris_data,
        provide_context=True,
    )
    #task for inference model
    inference = PythonOperator(
        task_id='run_inference',
        python_callable=run_inference,
        provide_context=True,
    )

    send_email = EmailOperator(
        task_id='send_success_email',
        to='ethingwillbefine@gmail.com',
        subject='✅ Iris Processing Completed for {{ ds }}',
        html_content='''
          <h3>DAG process_iris completed successfully!</h3>
          <p><strong>Execution date:</strong> {{ ds }}</p>
          <p><strong>Run ID:</strong> {{ run_id }}</p>
          <hr>

          <h4>📊 Model Training Results:</h4>
          <ul>
              <li>Full model accuracy: {{ ti.xcom_pull(task_ids='train_ml_model')['full_model_accuracy'] | round(4) }}</li>
              <li>Top 5 features accuracy: {{ ti.xcom_pull(task_ids='train_ml_model')['top5_model_accuracy'] | round(4) }}</li>
              <li>Top features: {{ ti.xcom_pull(task_ids='train_ml_model')['top_features'] | join(', ') }}</li>
          </ul>

          <h4>🔮 Inference Results:</h4>
          <ul>
              <li>Total predictions: {{ ti.xcom_pull(task_ids='run_inference')['total_predictions'] }}</li>
              <li>Predictions by species:
                  <ul>
                  {% for species, count in ti.xcom_pull(task_ids='run_inference')['predictions_summary'].items() %}
                      <li>{{ species }}: {{ count }}</li>
                  {% endfor %}
                  </ul>
              </li>
          </ul>

          <h4>📝 Sample Predictions:</h4>
          <table border="1" cellpadding="5">
              <tr>
                  <th>Predicted Species</th>
                  <th>Prob Setosa</th>
                  <th>Prob Versicolor</th>
                  <th>Prob Virginica</th>
              </tr>
              {% for row in ti.xcom_pull(task_ids='run_inference')['sample_predictions'] %}
              <tr>
                  <td>{{ row['predicted_species'] }}</td>
                  <td>{{ row['probability_setosa'] | round(3) }}</td>
                  <td>{{ row['probability_versicolor'] | round(3) }}</td>
                  <td>{{ row['probability_virginica'] | round(3) }}</td>
              </tr>
              {% endfor %}
          </table>

          <hr>
          <p>Check full results in database: <code>ml_results.iris_model_metrics</code></p>
          ''',
    )

    dbt_transform >> train_model >> inference >> send_email