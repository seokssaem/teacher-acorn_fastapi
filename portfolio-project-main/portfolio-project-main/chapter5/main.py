"""FastAPI 프로그램 - 5장"""

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

import crud, schemas
from database import SessionLocal

api_description = """
이 API는 Sports World Central(SWC) 판타지 풋볼 API의 정보를 읽기 전용으로 제공합니다. 
제공되는 엔드포인트는 다음과 같습니다.

## 분석(Analytics)
API의 상태와 리그, 팀, 선수 수에 대한 정보를 제공합니다.

## 선수(Player)
NFL 선수 목록을 조회하거나, 특정 player_id를 이용해 개별 선수 정보를 제공합니다.

## 점수(Scoring)
NFL 선수의 경기 성적과 해당 성적을 기반으로 한 SWC 리그 판타지 점수를 제공합니다.

## 멤버십(Membership)
SWC 판타지 풋볼 리그 전체와 각 리그에 속한 팀에 대한 정보를 제공합니다.
"""

# OpenAPI 명세에 추가 세부 정보를 포함한 FastAPI 앱 생성자
app = FastAPI(
    description=api_description,
    title="Sports World Central(SWC) 판타지 풋볼 API",
    version="0.1",
)

# 종속성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get(
    "/",
    summary="SWC 판타지 풋볼 API가 실행 중인지 확인합니다.",
    description="""이 엔드포인트를 사용해 API가 실행 중인지 확인합니다. 다른 호출을 하기 전에 먼저 이 엔드포인트를 확인하면 API가 정상 작동하는지 알 수 있습니다.""",
    response_description="메시지가 포함된 JSON 레코드입니다. API가 실행 중이면 성공 메시지를 반환합니다.",
    operation_id="v0_health_check",
    tags=["analytics"],
)
async def root():
    return {"message": "API 상태 확인 성공"}


@app.get(
    "/v0/players/",
    summary="요청 매개변수에 해당하는 모든 SWC 선수 정보를 가져옵니다.",
    response_model=list[schemas.Player],
    description="""이 엔드포인트를 사용해 SWC 선수 목록을 조회합니다. 매개변수를 이용해 목록을 필터링할 수 있습니다. 이름은 고유하지 않습니다. skip과 limit을 사용해 API 페이징을 수행합니다. 선수 수를 셀 때는 Player ID 값을 사용하지 않습니다. ID는 순차적으로 보장되지 않습니다.""",
    response_description="SWC 판타지 풋볼에 등록된 NFL 선수 목록입니다. 팀에 속해 있지 않아도 선수 목록을 제공합니다.",
    operation_id="v0_get_players",
    tags=["players"],
)
def read_players(
    skip: int = Query(
        0, description="API 호출 시작 부분에서 건너뛸 항목 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 레코드 이후 반환할 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="변경 기준 날짜입니다. 이 날짜 이후에 변경된 레코드만 반환합니다.",
    ),
    first_name: str = Query(
        None, description="반환할 선수의 이름입니다."
    ),
    last_name: str = Query(None, description="반환할 선수의 성입니다."),
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
    summary="SWC 내부 선수 ID를 사용하여 개별 선수 정보를 가져옵니다.",
    description="다른 API 호출(v0_get_players 등)에서 얻은 SWC 선수 ID를 이용해 해당 선수를 조회할 수 있습니다.",
    response_description="선택한 NFL 선수 정보입니다.",
    operation_id="v0_get_players_by_player_id",
    tags=["players"],
)
def read_player(player_id: int, db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id=player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="선수를 찾을 수 없습니다!")
    return player


@app.get(
    "/v0/performances/",
    response_model=list[schemas.Performance],
    summary="요청 매개변수에 해당하는 모든 주간 성적을 가져옵니다.",
    description="""이 엔드포인트를 사용해 SWC에서 선수의 주간 성적 목록을 조회합니다. skip과 limit을 사용해 페이징을 수행합니다. Performance ID는 내부 ID이므로 개수 계산이나 로직에 사용하지 않습니다. 순차적으로 보장되지 않습니다.""",
    response_description="주간 성적 목록입니다. 여러 선수의 성적을 포함할 수 있습니다.",
    operation_id="v0_get_performances",
    tags=["scoring"],
)
def read_performances(
    skip: int = Query(
        0, description="API 호출 시작 부분에서 건너뛸 항목 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 레코드 이후 반환할 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="변경 기준 날짜입니다. 이 날짜 이후에 변경된 레코드만 반환합니다.",
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
    summary="리그 ID에 해당하는 리그 정보를 가져옵니다.",
    description="""이 엔드포인트를 사용해 제공된 league_id와 일치하는 리그 정보를 조회합니다.""",
    response_description="1개의 SWC 리그입니다.",
    operation_id="v0_get_league_by_league_id",
    tags=["membership"],
)
def read_league(league_id: int, db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id=league_id)
    if league is None:
        raise HTTPException(status_code=404, detail="리그를 찾을 수 없습니다!")
    return league


@app.get(
    "/v0/leagues/",
    response_model=list[schemas.League],
    summary="요청 매개변수에 해당하는 SWC 판타지 풋볼 리그 정보를 가져옵니다.",
    description="""이 엔드포인트를 사용해 SWC 판타지 풋볼 리그 목록을 조회합니다. skip과 limit을 사용해 페이징을 수행합니다. 리그 이름은 고유하지 않습니다. League ID는 내부 ID이므로 개수 계산이나 로직에 사용하지 않습니다. 순차적으로 보장되지 않습니다.""",
    response_description="SWC 판타지 풋볼 웹사이트의 리그 목록입니다.",
    operation_id="v0_get_leagues",
    tags=["membership"],
)
def read_leagues(
    skip: int = Query(
        0, description="API 호출 시작 부분에서 건너뛸 항목 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 레코드 이후 반환할 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="변경 기준 날짜입니다. 이 날짜 이후에 변경된 레코드만 반환합니다.",
    ),
    league_name: str = Query(
        None, description="반환할 리그 이름입니다. SWC에서 고유하지 않습니다."
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
    summary="요청 매개변수에 해당하는 SWC 판타지 풋볼 팀 정보를 가져옵니다.",
    description="""이 엔드포인트를 사용해 SWC 판타지 풋볼 팀 목록을 조회합니다. skip과 limit을 사용해 페이징을 수행합니다. 팀 이름은 고유하지 않습니다. 다른 쿼리에서 얻은 Team ID를 이 쿼리의 Team ID와 매칭할 수 있습니다. Team ID는 내부 ID이므로 개수 계산이나 로직에 사용하지 않습니다. 순차적으로 보장되지 않습니다.""",
    response_description="SWC 판타지 풋볼 웹사이트의 팀 목록입니다.",
    operation_id="v0_get_teams",
    tags=["membership"],
)
def read_teams(
    skip: int = Query(
        0, description="API 호출 시작 부분에서 건너뛸 항목 수입니다."
    ),
    limit: int = Query(
        100, description="건너뛴 레코드 이후 반환할 레코드 수입니다."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="변경 기준 날짜입니다. 이 날짜 이후에 변경된 레코드만 반환합니다.",
    ),
    team_name: str = Query(
        None,
        description="반환할 팀 이름입니다. SWC 전체에서 고유하지 않으나, 리그 내부에서는 고유합니다.",
    ),
    league_id: int = Query(
        None, description="반환할 팀이 속한 리그 ID입니다. SWC에서 고유합니다."
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
    summary="SWC 판타지 풋볼의 리그, 팀, 선수 수를 가져옵니다.",
    description="""이 엔드포인트를 사용해 SWC 판타지 풋볼의 리그, 팀, 선수 수를 확인합니다. 다른 조회 엔드포인트의 skip과 limit 매개변수과 함께 사용합니다. 개수를 확인하려면 다른 API 대신 이 엔드포인트를 사용합니다.""",
    response_description="SWC 판타지 풋볼의 리그, 팀, 선수 수입니다.",
    operation_id="v0_get_counts",
    tags=["analytics"],
)
def get_count(db: Session = Depends(get_db)):
    counts = schemas.Counts(
        league_count=crud.get_league_count(db),
        team_count=crud.get_team_count(db),
        player_count=crud.get_player_count(db),
    )
    return counts