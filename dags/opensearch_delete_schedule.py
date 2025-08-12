# 표준 lib
import json

# external packages
import pendulum
import requests

# airflow
from airflow.decorators import dag, task

# internal modules
from config.opensearch import (
    OPENSEARCH_URL 
    , AUTH
)


@dag(
    dag_id="opensearch_delete_schedule",
    schedule="@hourly",
    start_date=pendulum.datetime(2025, 8, 1, tz="Asia/Seoul"),
    tags=["opensearch", "index", "delete"],
    catchup=False,
) 
def opensearch_delete_schedule():

    @task
    def delete_opensearch_index():

        response = requests.delete(f"{OPENSEARCH_URL}/kakao_*"
                                , auth=AUTH 
                                , json={}
                                , verify=False)

        if response.ok:
            response_json = response.json()
            print(response_json)   


    # DAG 흐름 설정
    delete_opensearch_index()

dag = opensearch_delete_schedule()