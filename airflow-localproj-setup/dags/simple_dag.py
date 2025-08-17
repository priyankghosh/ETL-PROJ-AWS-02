from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello_world():
    print("Hello from Airflow!")

with DAG("simple_dag",
         start_date=datetime(2023, 1, 1),
         schedule_interval="@once",
         catchup=False) as dag:

    task = PythonOperator(
        task_id="say_hello",
        python_callable=hello_world
    )
