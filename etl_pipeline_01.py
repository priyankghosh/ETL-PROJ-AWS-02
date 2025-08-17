from airflow import DAG
from datetime import timedelta, datetime
import json
import requests
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor


# Load api config file
with open('/home/ubuntu/airflow/api_config.json', 'r') as con_file:
    api_host_key = json.load(con_file)

#dt_string_definition
now = datetime.now()
dt_now_string = now.strftime("%Y-%m-%d_%H-%M-%S")

# Define the S3 bucket
s3_bucket = 'cleaned-data-csv-intermediate-02-bucket'

def extract_api_data_fn(**kwargs):
    api_url = kwargs.get('api_url')
    querystring = kwargs.get('querystring')
    headers = kwargs.get('headers')
    dt_string = kwargs.get('date_string')

    # Call the API and extract data
    response = requests.get(api_url, headers=headers, params=querystring)
    data = response.json()

    #Specify output file path
    output_file_path = f"/home/ubuntu/response_data_{dt_string}.json"
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

    load_to_S3 = BashOperator(
        task_id='tsk_load_to_S3',
        bash_command='aws s3 mv {{ ti.xcom_pull(task_ids="tsk_extract_api_data")[0]}} s3://etl-proj-01-raw/',
    )

    is_file_in_S3_available = S3KeySensor(
        task_id='tsk_is_file_in_S3_available',
        bucket_key='{{ ti.xcom_pull(task_ids="tsk_extract_api_data")[1] }}',
        bucket_name=s3_bucket,
        aws_conn_id='aws_s3_conn',
        wildcard_match=False, # Set this to True if u want to use wildcards in the prefix
        timeout=60, # Optional : Timeout for the sensor (in seconds)
        poke_interval=5, # Optional : Time interval between S3 checks (in seconds)
    )
    
    transfer_S3_to_redshift = S3ToRedshiftOperator(
        task_id='tsk_transfer_S3_to_redshift',
        schema='PUBLIC',
        table='housingdata',
        copy_options=['CSV IGNOREHEADER 1'],
        aws_conn_id='aws_s3_conn',
        redshift_conn_id='conn_id_redshift',
        s3_bucket=s3_bucket,
        s3_key='{{ ti.xcom_pull(task_ids="tsk_extract_api_data")[1] }}',
        dag=dag
    )

    extract_api_data >> load_to_S3 >> is_file_in_S3_available >> transfer_S3_to_redshift