"""FastAPI 프로그램 - 2부"""

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date


import crud, schemas
from database import SessionLocal

api_description = """
이 API는 Sports World Central(SWC) 판타지 풋볼 API의 정보를 읽기 전용(Read-only)으로 제공합니다.
엔드포인트는 다음과 같이 구성되어 있습니다.

## 분석(Analytics)
API의 상태와 리그, 팀, 선수 수에 대한 통계를 제공합니다.

## 선수(Player)
NFL 선수 목록과 개별 선수 정보를 제공합니다.

## 성적(Scoring)
SWC 리그 채점 방식을 기준으로 계산한 NFL 선수들의 주간 성적(판타지 점수 포함)을 제공합니다.

## 멤버십(Membership)
SWC 판타지 풋볼 리그와 각 리그에 속한 팀 정보를 제공합니다.

## 일반(General)
SWC 판타지 풋볼 플랫폼 전반에 대한 정보를 제공합니다.
"""

# OpenAPI 명세에 표시될 추가 설명이 포함된 FastAPI 애플리케이션 생성자
app = FastAPI(
    description=api_description,
    title="Sports World Central (SWC) 판타지 풋볼 API",
    version="0.2",
)


# 데이터베이스 세션을 제공하는 종속성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get(
    "/",
    summary="SWC 판타지 풋볼 API의 상태를 확인합니다.",
    description="""이 엔드포인트를 사용해 API가 실행 중인지 확인합니다. 
    다른 엔드포인트를 호출하기 전에 먼저 호출해 API의 상태를 확인할 수도 있습니다.""",
    response_description="메시지가 포함된 JSON 응답입니다. API가 실행 중이면 메시지가 '성공(successful)'이라고 표시됩니다.",
    operation_id="v0_health_check",
    tags=["analytics"],
)
async def root():
    return {"message": "API 상태 확인 성공"}


@app.get(
    "/v0/players/",
    response_model=list[schemas.Player],
    summary="요청한 조건을 모두 만족하는 모든 SWC 선수를 조회합니다.",
    description="""이 엔드포인트를 사용해 SWC 선수을 조회합니다. 매개변수를 사용해 결과를 필터링할 수 있습니다. 
    선수 이름은 고유하지 않으며, skip과 limit를 사용해 쪽매김을 수행합니다. 
    Player ID는 순서가 보장되지 않으므로 선수 숫자를 세는 데 사용해서는 안됩니다.""",
    response_description="SWC 판타지 풋볼에 등록된 NFL 선수 목록으로, 선수는 특정 팀에 소속되어 있지 않을 수도 있습니다.",
    operation_id="v0_get_players",
    tags=["players"],
)
def read_players(
    skip: int = Query(
        0, description="API 호출 시 건너뛸 항목의 개수"
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후 반환할 항목의 최대 개수"
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="항목을 반환할 최소 변경 날짜. 이 날짜 이전에 변경된 항목은 제외합니다.",
    ),
    first_name: str = Query(
        None, description="반환할 선수의 이름"
    ),
    last_name: str = Query(None, description="반환할 선수의 성"),
    db: Session = Depends(get_db),
):
    players = crud.get_players(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        first_name=first_name,
        last_name=last_name,
    )
    return players


@app.get(
    "/v0/players/{player_id}",
    response_model=schemas.Player,
    summary="SWC 내부에서 사용되는 Player ID를 사용해 개별 선수를 조회합니다.",
    description="다른 API 호출(예: v0_get_players)에서 얻은 SWC Player ID로 개별 선수를 조회합니다.",
    response_description="NFL 선수에 대한 정보",
    operation_id="v0_get_players_by_player_id",
    tags=["players"],
)
def read_player(player_id: int, db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id=player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="선수를 찾을 수 없습니다.")
    return player


@app.get(
    "/v0/performances/",
    response_model=list[schemas.Performance],
    summary="요청 조건을 모두 만족하는 모든 주간 성적을 조회합니다.",
    description="""이 엔드포인트를 사용해 SWC에서 선수의 주간 성적을 조회합니다. skip과 limit를 사용해 쪽매김을 수행합니다. 
    Performance ID는 SWC 내부에서 사용되는 ID로 순서가 보장되지 않으므로 선수 숫자를 세거나 논리 계산에 사용해서는 안됩니다.""",
    operation_id="v0_get_performances",
    tags=["scoring"],
)
def read_performances(
    skip: int = Query(
        0, description="API 호출 시 건너뛸 항목의 개수"
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후 반환할 항목의 최대 개수"
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="항목을 반환할 최소 변경 날짜. 이 날짜 이전에 변경된 항목은 제외합니다.",
    ),
    db: Session = Depends(get_db),
):
    performances = crud.get_performances(
        db, skip=skip, limit=limit, min_last_changed_date=minimum_last_changed_date
    )
    return performances


@app.get(
    "/v0/leagues/{league_id}",
    response_model=schemas.League,
    summary="League ID로 개별 리그를 조회힙니다.",
    description="""이 엔드포인트를 사용해 League ID로 리그를 조회합니다.""",
    response_description="SWC 리그에 대한 정보",
    operation_id="v0_get_league_by_league_id",
    tags=["membership"],
)
def read_league(league_id: int, db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id=league_id)
    if league is None:
        raise HTTPException(status_code=404, detail="리그를 찾을 수 없습니다.")
    return league


@app.get(
    "/v0/leagues/",
    response_model=list[schemas.League],
    summary="요청 조건을 모두 만족하는 모든 SWC 판타지 풋볼 리그를 조회합니다.",
    description="""이 엔드포인트를 사용해 SWC 판타지 풋볼 리그을 조회합니다. 리그 이름은 고유하지 않으며, skip과 limit를 사용해 쪽매김을 수행합니다. 
    League ID는 SWC 내부에서 사용되는 ID로 순서가 보장되지 않으므로 선수 숫자를 세거나 논리 계산에 사용해서는 안됩니다.""",
    response_description="SWC 판타지 풋볼 웹사이트에 등록된 리그 목록",
    operation_id="v0_get_leagues",
    tags=["membership"],
)
def read_leagues(
    skip: int = Query(
        0, description="API 호출 시 건너뛸 항목의 개수"
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후 반환할 항목의 최대 개수"
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="항목을 반환할 최소 변경 날짜. 이 날짜 이전에 변경된 항목은 제외합니다.",
    ),
    league_name: str = Query(
        None, description="리그 이름. SWC에서는 고유하지 않습니다. "
    ),
    db: Session = Depends(get_db),
):
    leagues = crud.get_leagues(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        league_name=league_name,
    )
    return leagues


@app.get(
    "/v0/teams/",
    response_model=list[schemas.Team],
    summary="요청 조건을 모두 만족하는 모든 판타지 풋볼 팀을 조회합니다.",
    description="""이 엔드포인트를 사용해 SWC 판타지 풋볼 팀 목록을 조회합니다. skip과 limit를 사용해 쪽매김을 수행합니다. 
    다른 API 호출에서 얻은 Team ID로 개별 팀을 조회합니다. 팀 이름은 고유하지 않으므로  팀 숫자를 세거나 논리 계산에 사용해서는 안됩니다.""",
    response_description="SWC 판타지 풋볼 웹사이트에 등록된 팀 목록",
    operation_id="v0_get_teams",
    tags=["membership"],
)
def read_teams(
    skip: int = Query(
        0, description="API 호출 시 건너뛸 항목의 개수"
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후 반환할 항목의 최대 개수"
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="항목을 반환할 최소 변경 날짜. 이 날짜 이전에 변경된 항목은 제외합니다.",
    ),
    team_name: str = Query(
        None,
        description="조회한 팀 이름. SWC 전체에서 고유하지 않지만, 리그 내에서는 고유합니다.",
    ),
    league_id: int = Query(
        None, description="조회한 팀의 League ID. SWC에서 고유합니다."
    ),
    db: Session = Depends(get_db),
):
    teams = crud.get_teams(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        team_name=team_name,
        league_id=league_id,
    )
    return teams


@app.get(
    "/v0/counts/",
    response_model=schemas.Counts,
    summary="SWC 판타지 풋볼의 리그, 팀, 선수 수를 조회합니다.",
    description="""이 엔드포인트를 사용해 SWC 판타지 풋볼의 리그, 팀, 선수 수를 조회합니다. 
    v0_get leagues, v0_get_teams 또는 v0_get_players에서 skip과 limit을 함께 사용할 수 있습니다. 
    다른 API를 호출하는 대신 이 엔드포인트를 사용해 개수를 조회할 수 있습니다.""",
    response_description="SWC 판타지 풋볼 웹사이트에 등록된 리그, 팀, 선수 집계 정보",
    operation_id="v0_get_counts",
    tags=["analytics"],
)

def get_count(db: Session = Depends(get_db)):
    counts = schemas.Counts(
        league_count=crud.get_league_count(db),
        team_count=crud.get_team_count(db),
        player_count=crud.get_player_count(db),
        week_count=crud.get_week_count(db), #v0.2
    )
    return counts

#v0.2
@app.get(
    "/v0/weeks/",
    response_model=list[schemas.Week],
    summary="요청 조건을 모두 만족하는 모든 SWC 주간 정보를 조회합니다.",
    description="""이 엔드포인트를 사용해 SWC 주 목록을 조회합니다. 매개변수를 사용해 결과를 필터링할 수 있습니다.
    skip과 limit를 사용해 쪽매김을 수행합니다.""",
    response_description="SWC 판타지 풋볼의 주간 정보",
    operation_id="v0_get_weeks",
    tags=["general"],
)
def read_weeks(
    skip: int = Query(
        0, description="API 호출 시 건너뛸 항목의 개수"
    ),
    limit: int = Query(
        100, description="건너뛴 항목 이후 반환할 항목의 최대 개수"
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="항목을 반환할 최소 변경 날짜. 이 날짜 이전에 변경된 항목은 제외합니다.",
    ),
    db: Session = Depends(get_db),
):
    weeks = crud.get_weeks(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
    )
    return weeks