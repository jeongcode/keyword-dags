# 표준 lib
import json

# external packages
import pendulum
import requests
from openai import OpenAI

# airflow
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.decorators import dag, task

# internal modules
from config.opensearch import (
    OPENSEARCH_URL 
    , AUTH
    , AI_API_KEY
)

def insert_recent_keyword_infos (keyword, main_keyword_infos):
    hook = PostgresHook(postgres_conn_id='postgres_default')

    update_sql = """
    UPDATE keyword.words
    SET relation_urls = %s::jsonb
    WHERE word = %s
    """
    
    json_str = json.dumps(main_keyword_infos) # dict -> JSON 문자열 변환   
    hook.run(update_sql, parameters=(json_str,keyword))

def get_main_keywords (keyword, url_list):
    messages = [
        {
            "role": "system",
            "content": (
                "The user delivers the url list to you."
                "Urls are the latest searches for specific keywords."
                "Please analyze the url contents of the user "
                "and let me know the five most relevant or meaningful keywords "
                "and the representative Url related to the keyword. "
            )
        },
        {
            "role": "user",
            "content": (
                " ".join(f'"{url}"' for url in url_list)
            ),
        },
    ]

    client = OpenAI(api_key=AI_API_KEY, base_url="https://api.perplexity.ai")

    # demo chat completion without streaming
    response = client.chat.completions.create(
        model="sonar",
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "string"},
                        "urls": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "keyword": {"type": "string"},
                                    "url": {"type": "string"}
                                },
                            },
                        }
                    },
                    "required": ["keywords", "urls"]
                }
            }
        }
    )

    data = response.to_dict()
    content = data["choices"][0]["message"]["content"]
    response_data = json.loads(content)

    return response_data


@dag(
    dag_id="kakao_keyword_agg",
    schedule="*/10 * * * *",
    start_date=pendulum.datetime(2025, 8, 1, tz="Asia/Seoul"),
    tags=["kakao", "keyword", "aggregation"],
    catchup=False,
) 
def kakao_keyword_agg():
    
    @task # get 키워드 리스트
    def get_keyword_list():
        hook = PostgresHook(postgres_conn_id='postgres_default')
        rows = hook.get_records("SELECT word FROM keyword.words words where is_deleted ='F';")
        keywords = [row[0] for row in rows]
        return keywords

    @task 
    def make_pairs(keywords: list):
        return [
            {"kw": kw}
            for kw in keywords
        ]

    @task
    def process_each_pair(pair):
        kw = pair["kw"]
        url_list = []

        # 1. 키워드 관련 최근 컨텐츠들 (최근 기준 : 최신순 100개, TODO : 날짜기준으로변경)
        response = requests.get(f"{OPENSEARCH_URL}/kakao_*/_search"
                                , auth=AUTH 
                                , json={
                                    "size" : 100,
                                    "_source": {
                                        "includes": [ "url" ]
                                    },
                                    "query":{
                                        "match": {
                                            "keyword": kw
                                        }
                                    }
                                }, verify=False)

        if response.ok:
            response_json = response.json()   

            url_list = [
                hit["_source"]["url"] 
                for hit in response_json.get("hits", {}).get("hits", []) 
                if "_source" in hit and "url" in hit["_source"]
            ]

        # 2. 컨텐츠 분석 후 가장 의미 있는 관련 키워드,url 5개 지정 (perplexity api)
        keywordInfos = get_main_keywords(kw, url_list)

        # 3. 해당 정보 활용 위한 rdb insert(history table 관리) 
        insert_recent_keyword_infos(kw, keywordInfos)


    # DAG 흐름 설정
    keywords = get_keyword_list()
    pairs = make_pairs(keywords)
    process_each_pair.expand(pair=pairs)

dag = kakao_keyword_agg()