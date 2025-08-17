from airflow import DAG
from datetime import timedelta, datetime
import json
import requests
from airflow.operators.python import PythonOperator


# Load api config file
with open('/opt/airflow/dags/api_config.json', 'r') as con_file:
    api_host_key = json.load(con_file)

#dt_string_definition
now = datetime.now()
dt_now_string = now.strftime("%Y-%m-%d_%H-%M-%S")

def extract_api_data_fn(**kwargs):
    api_url = kwargs.get('api_url')
    querystring = kwargs.get('querystring')
    headers = kwargs.get('headers')
    dt_string = kwargs.get('date_string')

    # Call the API and extract data
    response = requests.get(api_url, headers=headers, params=querystring)
    data = response.json()

    #Specify output file path
    output_file_path = f"/opt/airflow/dags/response_data_{dt_string}.json"
    file_str = f'response_data_{dt_string}.csv'

    #Write JSON response to a file
    with open(output_file_path, "w") as opt_file:
        json.dump(data, opt_file, indent=4)  #indent for pretty formatting
    output_list = [output_file_path, file_str]

    return output_list


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 8, 16),
    'email': ['zoolander.demote909@passinbox.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=5),
}

with DAG(
    dag_id='etl_pipeline_01',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False) as dag:

    extract_api_data = PythonOperator(
        task_id='tsk_extract_api_data',
        python_callable=extract_api_data_fn,
        op_kwargs={
            'api_url': 'https://zillow56.p.rapidapi.com/search',
            'querystring': {"location": "houston, tx", "output": "json", "status": "forSale", "sortSelection": "priorityscore", "listing_type": "by_agent", "doz": "any"},
            'headers': api_host_key,
            'date_string': dt_now_string
        }
    )
