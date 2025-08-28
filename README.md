## 1. 프로젝트 개요

- 프로젝트명 : 사용자 관심 키워드 관련 최신 웹 데이터 수집.적재.집계하기
- 개발 기간 : 50h
- 참여 인원 : 1
- 프로젝트 목적 및 배경 : 데이터를 수집,관리할 때 일련의 관리 과정을 자동화하는 툴 중 하나인 Airflow를 사용해보는 것을 목적으로 한다. 사용자가 관심이 있는 키워드에 대한 최신 웹 데이터를 주기적으로 수집.적재하고 키워드와 관련된 핵심 단어 및 웹 사이트 정보를 알 수 있다.

## 2. 기술 스택

- 사용한 기술 스택 (언어, 프레임워크, 데이터베이스, 툴 등) :<br />
  >언어 : javascript, java, python<br />
  >프레임워크, 툴 : React, Spring, Apache Airflow<br />
  >데이터베이스 : Postgresql<br />
  >검색엔진 : Opensearch<br />
  >버전 : react(19), node(22.17.1), java(17), python(3.12), airflow(3.0.3), Opensearch(3.1.0) => 최신/사용률/LTS/각 개발환경 상성 고려하여 알맞은 버전으로 선정
  >배포 : Github, Github Actions, AWS

## 3. 상세 구현 내용

- 주요 기능 구현 내용 설명<br />
  >사용자 단어 등록<br />
  >등록된 단어에 관련된 웹 데이터 10분마다 주기적 수집(외부 검색 api 사용) 및 적재(Opensearch)<br />
  >수집된 데이터들 대상으로 관련 핵심 단어 및 url 추출(핵심 단어 선정 기준 : perplexity ai api 사용)<br />
  >수집된 데이터들에 대한 핵심단어 및 url 내용, 변경 이력 조회 기능<br /><br />
  
- 성능 개선 또는 문제 해결 사례<br />
  >데이터 정합성 유지 - Opensearch 중복 데이터 적재 방지 위해 데이터 별로 식별되는 url로 document 별 id 생성<br />
  >Airflow dag 내 task 실행시 동적 변수를 참조하게 될 경우, 실행순서 관련 오류가 나 Dynamic task mapping으로 해결하고 관련 기능에 대해 알아보게 되었다.<br /><br />
  
- 코드 설계, 아키텍처, 데이터베이스 설계 등 기술적 세부 사항<br /><br />

(사용자 화면)<br />
<img width="1327" height="957" alt="Image" src="https://github.com/user-attachments/assets/303aad04-5db3-40ed-aa93-cea81334e821" />

(Opensearch 모니터링 대시보드)<br />
<img width="2000" height="1045" alt="Image" src="https://github.com/user-attachments/assets/8e57b4f5-05bd-4ebd-920b-141d4bc9f7dc" />

(postgresql 테이블)<br />
<img width="546" height="334" alt="Image" src="https://github.com/user-attachments/assets/ff41b660-c875-44e5-9f20-334f71dafb08" />

(aws 아키텍처)
<img width="968" height="517" alt="Image" src="https://github.com/user-attachments/assets/39ae2a69-8616-42d2-91bc-ed66b156333d" />

(sw 구성도)<br />
![Image](https://github.com/user-attachments/assets/78958686-7ef8-454f-914f-fe93c8037920)

## 4. 결과 및 성과

- 프로젝트 결과(배포, 사용자 수, 매출 증대 등 수치, 지표) : aws 배포/배포자동화, 개인 프로젝트<br />
- 얻은 경험 및 배운 점 : 데이터를 수집.적재를 자동화하는 일련의 과정을 경험하고 클라우드 배포 및 배포를 자동화를 직접 적용해보면서 운영환경에 대한 생각을 해보는 계기가 되었다.<br /><br />

## 5. 기타 추가 요소

- 향후 개선 사항이나 보완 계획 : <br />
1. 추가 상세 테스트 및 오류 모니터링 관련 사항 미비 <br />
2. 클라우드 배포, 배포 자동화 <br />
   - 도메인 및 인증서 적용
   - aws 배포, 배포 자동화 github actions 배포 자동화 적용 완료(8월:+12h)
3. 성능향상을 위한 소스 개선, 파이프라인/서버 관리 <br />
등에 대해 알아보면 좋을 것 같다.

- 프로젝트 관련 링크 (GitHub, 데모 페이지 등)<br />
  전체 소스 github : https://github.com/stars/jeongcode/lists/keyword-prj
