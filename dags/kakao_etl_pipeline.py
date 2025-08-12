# 표준 lib
import re
import json
import hashlib

# external packages
import pendulum
import requests
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

# airflow
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.decorators import dag, task

# internal modules
from config.opensearch import (
    INDEXES 
    , KAKAO_DOMAIN
    , KAKAO_API_KEY 
    , KAKAO_API_ENDPOINTS
    , OPENSEARCH_URL 
    , AUTH
    , HOST_DOMAIN
)

transliter = Transliter(academic)

def make_hashid(doc) :
    id_fields = [
        doc.get('url', '') 
    ]
    
    if all(not f for f in id_fields):
        id_source = json.dumps(doc, sort_keys=True)
    else:
        id_source = '|'.join(id_fields)

    doc_id = hashlib.sha1(id_source.encode('utf-8')).hexdigest() # 해시값 생성
    return doc_id

def bulk_insert_to_opensearch(index, kw, ep, data):
    index_name = index
    keyword = kw
    endpoint = ep

    if not data or 'documents' not in data:
        print(f"[{keyword}][{endpoint}] No data to insert")
        return

    documents = data["documents"]
    if not documents:
        print(f"[{keyword}][{endpoint}] Empty documents list")
        return

    bulk_body = []

    for doc in documents:
        doc_id = make_hashid(doc)

        doc['keyword'] = keyword

        bulk_body.append(
            {
                "_index": index_name,
                "_id": doc_id,
                "_source": doc
            }
        )
    
    client = OpenSearch(
        hosts=[{"host": HOST_DOMAIN, "port": 9200}],
        http_auth= AUTH,
        use_ssl=True,
        verify_certs=False,
    )
    
    if bulk_body:
        success, _ = bulk(client, bulk_body)
        print(f"[{keyword}][{endpoint}] Inserted {success} documents")
    else:
        print(f"[{keyword}][{endpoint}] No valid documents to insert")

def get_index_name(endpoint):
    if endpoint == "v2/search/web":
        return "kakao_web"
    elif endpoint == "v2/search/blog" :
        return "kakao_blog"
    else :        
        return "kakao_etc"
    
def safe_task_id_from_korean(keyword: str, endpoint: str):
    romanized = transliter.translit(keyword) # 한글 키워드 로마자로 변환
    romanized = romanized.lower().strip() # 소문자 변환 및 앞뒤 공백 제거
    romanized = re.sub(r'[^a-z0-9]+', '_', romanized) # 로마자 이외 문자 모두 밑줄(_)로 치환 (공백, 특수문자 등 모두)
    
    ep_safe = endpoint.lower().replace('/', '_') # 슬래시(/)를 밑줄(_)로 변경 & endpoint 소문자화
    
    task_id = f"task_{romanized}_{ep_safe}" # 두 부분 조합(중복 밑줄 제거)
    task_id = re.sub(r'_+', '_', task_id)
    task_id = task_id.strip('_')  # 시작/끝 밑줄 제거
    
    if len(task_id) > 250: # 길이 제한 처리 (최대 250자)
        task_id = task_id[:250]
    
    return task_id

@dag(
    dag_id="kakao_etl_pipeline",
    schedule="*/10 * * * *",
    start_date=pendulum.datetime(2025, 7, 20, tz="Asia/Seoul"),
    tags=["kakao", "api", "pipeline"],
    catchup=False,
) 
def kakao_etl_pipeline():

    @task # opensearch : 인덱스/설정 생성
    def create_indexes_if_absent():
        for index in INDEXES:
            index_name = index["name"]
            body = index["body"]

            response = requests.put(f"{OPENSEARCH_URL}/{index_name}", auth=AUTH, json=body, verify=False)
            if response.status_code == 400 and "resource_already_exists_exception" in response.text:
                print(f"Index '{index_name}' already exists. Skipping.")
            elif response.ok:
                print(f"Index '{index_name}' created successfully.")
            else:
                response.raise_for_status()
    
    @task # get 설정한 키워드 리스트
    def get_keyword_list():
        hook = PostgresHook(postgres_conn_id='postgres_default')
        rows = hook.get_records("SELECT word FROM keyword.words words where is_deleted ='F';")
        keywords = [row[0] for row in rows]
        return keywords

    @task 
    def make_pairs(keywords: list):
        return [
            {"kw": kw, "ep": ep}
            for kw in keywords
            for ep in KAKAO_API_ENDPOINTS
        ]
    
    @task
    def process_each_pair(pair):
        kw = pair["kw"]
        ep = pair["ep"]

        # 1. 데이터 받아오기
        url = f"{KAKAO_DOMAIN}/{ep}"

        
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        resp = requests.get(url, headers=headers, params={"query": kw, "sort" : "recency"})
        if resp.status_code != 200:
            print(f"API {ep} not available for {kw}")
            return

        result = resp.json()

        # 2. OpenSearch bulk insert
        bulk_insert_to_opensearch(get_index_name(ep), kw, ep, result)


    # DAG 흐름 설정
    create_indexes_if_absent()
    keywords = get_keyword_list()
    pairs = make_pairs(keywords)
    process_each_pair.expand(pair=pairs)

dag = kakao_etl_pipeline()