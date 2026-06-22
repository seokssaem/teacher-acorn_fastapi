import logging
import json
from airflow.hooks.base import BaseHook 

def upsert_player_data(player_json):
    import sqlite3
    import pandas as pd

    # Airflow UI에서 정의한 데이터베이스 연결 정보 가져오기
    database_conn_id = 'analytics_database'
    connection = BaseHook.get_connection(database_conn_id)
    
    sqlite_db_path = connection.schema

    if player_json:

        player_data = json.loads(player_json)
        
        # SQLite 연결은 콘텍스트 매니저로 관리한다
        with sqlite3.connect(sqlite_db_path) as conn:
            cursor = conn.cursor()

            # 각 선수 성적을 'player' 테이블에 삽입 또는 갱신
            for player in player_data:
                try:
                    cursor.execute("""
                        INSERT INTO player (
                            player_id, gsis_id, first_name, last_name, 
                            position, last_changed_date
                        ) 
                        VALUES (?, ?, ?, ?, ?, ?) 
                        ON CONFLICT(player_id) DO UPDATE
                        SET
                            gsis_id = excluded.gsis_id,
                            first_name = excluded.first_name,
                            last_name = excluded.last_name,
                            position = excluded.position,
                            last_changed_date = excluded.last_changed_date
                    """, (
                        player['player_id'], player['gsis_id'], 
                        player['first_name'], 
                        player['last_name'], 
                        player['position'], 
                        player['last_changed_date']
                    ))
                except Exception as e:
                    logging.error(
                        f"Failed to insert player {player['player_id']}: {e}")
                    raise
                    
    else:
        logging.warning("선수 데이터를 찾을 수 없습니다.")
        raise ValueError(
            "선수 데이터를 찾을 수 없습니다. 데이터 누락으로 태스크가 실패했습니다.")
