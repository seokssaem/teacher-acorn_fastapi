import datetime
import logging
from airflow.decorators import dag
from airflow.providers.http.operators.http import HttpOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from shared_functions import upsert_player_data


def health_check_response(response):
    logging.info(f"Response status code: {response.status_code}")
    logging.info(f"Response body: {response.text}")
    return response.status_code == 200 and response.json() == {
        "message": "API 상태 확인 성공"
    }


def insert_update_player_data(**context):

    player_json = context["ti"].xcom_pull(task_ids="api_player_query")

    if player_json:
        upsert_player_data(player_json)

    else:
        logging.warning("선수 데이터를 찾지 못했습니다.")


@dag(start_date=datetime.datetime(2024, 8, 7), schedule_interval=None, catchup=False)
def recurring_player_api_insert_update_dag():
    api_health_check_task = HttpOperator(
        task_id="check_api_health_check_endpoint",
        http_conn_id="sportsworldcentral_url",
        endpoint="/",
        method="GET",
        headers={"Content-Type": "application/json"},
        response_check=health_check_response,
    )

    # Airflow WEB UI에서 아래 에러 발생 시 최소 변경 날짜 변수를 추가해야 함
    #
    # DAG Import Errors (1)expand_less expand_moreBroken DAG: 
    # [/opt/airflow/dags/recurring_player_api_insert_update_dag.py] Traceback (most recent call last): 
    # File "/opt/airflow/dags/recurring_player_api_insert_update_dag.py", line 40, 
    # in recurring_player_api_insert_update_dag temp_min_last_change_date = Variable.get("temp_min_last_change_date")
    #  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 
    # File "/home/airflow/.local/lib/python3.12/site-packages/airflow/models/variable.py", line 145, 
    # in get raise KeyError(f"Variable {key} does not exist") KeyError: 'Variable temp_min_last_change_date does not exist'
    # 
    # 
    # temp_min_last_change_date = Variable.get("temp_min_last_change_date")
    temp_min_last_change_date = Variable.get("temp_min_last_change_date", default_var="2024-01-01")

    api_player_query_task = HttpOperator(
        task_id="api_player_query",
        http_conn_id="sportsworldcentral_url",
        endpoint=(
            f"/v0/players/?skip=0&limit=100000&minimum_last_changed_date="
            f"{temp_min_last_change_date}"
        ),
        method="GET",
        headers={"Content-Type": "application/json"},
    )

    player_sqlite_upsert_task = PythonOperator(
        task_id="player_sqlite_upsert",
        python_callable=insert_update_player_data,
        provide_context=True,
    )

    # 태스크 실행 순서 지정
    api_health_check_task >> api_player_query_task >> player_sqlite_upsert_task


# DAG 인스턴스화
dag_instance = recurring_player_api_insert_update_dag()
