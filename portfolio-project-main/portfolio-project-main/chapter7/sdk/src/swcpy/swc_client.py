import httpx
import swcpy.swc_config as config
from .schemas import League, Team, Player, Performance, Counts
from typing import List
import backoff
import logging
logger = logging.getLogger(__name__)

class SWCClient:
    """SportsWorldCentral API와 상호 작용하는 클라이언트 클래스

    이 SDK 클래스는 SWC 판타지 풋볼 API를 보다 쉽게 사용할 수 있도록 설계됐다.
    모든 API 기능을 지원하며, 데이터 검증이 완료된 타입을 반환한다.

    사용 예시:

        client = SWCClient()
        response = client.get_health_check()

    """

    # 주요 API 엔드포인트 정의
    HEALTH_CHECK_ENDPOINT = "/"
    LIST_LEAGUES_ENDPOINT = "/v0/leagues/"
    LIST_PLAYERS_ENDPOINT = "/v0/players/"
    LIST_PERFORMANCES_ENDPOINT = "/v0/performances/"
    LIST_TEAMS_ENDPOINT = "/v0/teams/"
    GET_COUNTS_ENDPOINT = "/v0/counts/"

    BULK_FILE_BASE_URL = (
        "https://raw.githubusercontent.com/[github ID]"
        + "/portfolio-project/main/bulk/"
    )



    def __init__(self, input_config: config.SWCConfig):
        """설정 객체를 통해 클라이언트 내부 속성을 초기화한다."""

        logger.debug(f"벌크 파일 베이스 URL: {self.BULK_FILE_BASE_URL}")

        logger.debug(f"입력 구성: {input_config}")

        self.swc_base_url = input_config.swc_base_url
        self.backoff = input_config.swc_backoff
        self.backoff_max_time = input_config.swc_backoff_max_time
        self.bulk_file_format = input_config.swc_bulk_file_format

        # 대용량 데이터 파일 이름 사전 초기화
        self.BULK_FILE_NAMES = {
            "players": "player_data",
            "leagues": "league_data",
            "performances": "performance_data",
            "teams": "team_data",
            "team_players": "team_player_data",
        }

        if self.backoff:
            self.call_api = backoff.on_exception(
                wait_gen=backoff.expo,
                exception=(httpx.RequestError, httpx.HTTPStatusError),
                max_time=self.backoff_max_time,
                jitter=backoff.random_jitter,
            )(self.call_api)

        # 파일 형식에 따라 확장자 자동 부여
        if self.bulk_file_format.lower() == "parquet":
            self.BULK_FILE_NAMES = {
                key: value + ".parquet" for key, value in self.BULK_FILE_NAMES.items()
            }
        else:
            self.BULK_FILE_NAMES = {
                key: value + ".csv" for key, value in self.BULK_FILE_NAMES.items()
            }

        logger.debug(f"벌크 파일 딕셔너리: {self.BULK_FILE_NAMES}")

    def call_api(self,
                api_endpoint: str,
                api_params: dict = None
            ) -> httpx.Response:
            """API를 호출하고 오류를 로깅한다."""

            # None 값을 제거해 유효한 매개 변수만 요청에 포함
            if api_params:
                api_params = {key: val for key, val in api_params.items() if val is not None}

            try:
                with httpx.Client(base_url=self.swc_base_url) as client: 
                    logger.debug(f"base_url: {self.swc_base_url}, api_endpoint: {api_endpoint}, api_params: {api_params}")
                    response = client.get(api_endpoint, params=api_params)
                    logger.debug(f"Response JSON: {response.json()}")
                    return response
                
            # HTTP 상태 코드 기반 예외 처리
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP 상태 오류 발생: {e.response.status_code} {e.response.text}"
                )
                raise

            # 기타 요청 관련 예외 처리
            except httpx.RequestError as e:
                logger.error(f"요청 중 오류 발생: {str(e)}")
                raise

    def get_health_check(self) -> httpx.Response:
        """
        API가 정상적으로 동작하는지 상태를 확인한다.

        API의 상태 확인 엔드포인트를 호출해,
        API가 정상적으로 실행 중일 경우 표준 응답 메시지를 반환한다.

        복잡한 API 호출을 수행하기 전에
        API의 상태를 점검하는 용도로 사용할 수 있다.

        반환값:
        - httpx.Response 객체: http 상태 코드, JSON 응답, 그 외 API로부터
                               받은 정보를 포함한다.

        """
        logger.debug("상태 확인 진입")
        endpoint_url = self.HEALTH_CHECK_ENDPOINT
        return self.call_api(endpoint_url)

    def list_leagues(
        self,
        skip: int = 0, 
        limit: int = 100, 
        minimum_last_changed_date: str = None,
        league_name: str = None,
    ) -> List[League]:
        """
        리그 정보를 조건에 따라 필터링해 반환한다.

        /v0/leagues 엔드포인트를 호출하고,
        반환된 JSON 데이터를 League 객체로 변환해 리스트로 반환한다.

        반환값:
        - schemas.League 객체의 리스트: 각 객체는 하나의 SportsWorldCentral
                                        판타지 리그를 나타낸다.
        """
        logger.debug("리그 정보 조회 진입")

        params = { 
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
            "league_name": league_name,
        }

        response = self.call_api(self.LIST_LEAGUES_ENDPOINT, params)
        return [League(**league) for league in response.json()]
    
        
    def get_league_by_id(self, league_id: int) -> League:
        """league_id와 일치하는 리그를 반환한다.

        v0/leagues/{league_id} 엔드포인트를 호출하고 리그 정보를 반환한다.

        반환값:
        - schemas.League 객체: 각 객체는 SportsWorldCentral 판타지 리그를 나타낸다. 

        """
        logger.debug("리그 ID 정보 조회 진입")
        # build URL
        endpoint_url = f"{self.LIST_LEAGUES_ENDPOINT}{league_id}"
        # make the API call
        response = self.call_api(endpoint_url)
        responseLeague = League(**response.json())
        return responseLeague


    def get_counts(self) -> Counts:
        """여러 엔드포인트의 개수를 반환한다.

        v0/counts 엔드포인트를 호출하고 Counts 객체를 반환한다.

        반환값:
        - Counts 객체: 각 객체는 API 내 요소들의 개수를 나타낸다.

        """
        logger.debug("개수 정보 조회 진입")

        response = self.call_api(self.GET_COUNTS_ENDPOINT)
        responseCounts = Counts(**response.json())
        return responseCounts

    def list_teams(
        self,
        skip: int = 0,
        limit: int = 100,
        minimum_last_changed_date: str = None,
        team_name: str = None,
        league_id: int = None,
    ):
        """매개변수로 필터링된 팀 목록을 반환한다.

        v0/teams 엔드포인트를 호출하고 팀 목록 객체를 반환한다.

        반환값:
        - schemas.Team 목록 객체: 각 객체는 SportsWorldCentral 판타지 리그의 팀 목록을 나타낸다.

                """

        logger.debug("팀 목록 정보 조회 진입")

        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
            "team_name": team_name,
            "league_id": league_id,
        }
        response = self.call_api(self.LIST_TEAMS_ENDPOINT, params)
        return [Team(**team) for team in response.json()]

    def list_players(
        self,
        skip: int = 0,
        limit: int = 100,
        minimum_last_changed_date: str = None,
        first_name: str = None,
        last_name: str = None,
    ):
        """매개변수로 필터링된 선수 목록을 반환한다.

        v0/players 엔드포인트를 호출하고 선수 목록 객체를 반환한다.

        반환값:
        - schemas.Player 목록 객체: 각 객체는 NFL 선수 목록을 나타낸다.

        """
        logger.debug("선수 목록 정보 조회 진입")

        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
            "first_name": first_name,
            "last_name": last_name,
        }

        response = self.call_api(self.LIST_PLAYERS_ENDPOINT, params)
        return [Player(**player) for player in response.json()]

    def get_player_by_id(self, player_id: int):
        """SWC 선수 ID와 일치하는 선수를 반환한다.

        v0/players/{player_id} 엔드포인트를 호출하고 선수 객체를 반환한다.

        반환값:
        - schemas.Player 객체: 각 객체는 NFL 선수를 나타낸다. 

        """
        logger.debug("선수 ID 정보 조회 진입")

        # URL 빌드
        endpoint_url = f"{self.LIST_PLAYERS_ENDPOINT}{player_id}"
        # API 호출 하기
        response = self.call_api(endpoint_url)
        responsePlayer = Player(**response.json())
        return responsePlayer

    def list_performances(
        self, skip: int = 0, limit: int = 100, minimum_last_changed_date: str = None
    ):
        """매개변수로 필터링된 성적 목록을 반환한다.

        v0/performances 엔드포인트를 호출하고 성적 목록 객체를 반환한다.

        반환값:
        - schemas.Performance 객체: 각 객체는 각 선수의 NFL 주간 점수를 나타낸다.

        """
        logger.debug("성적 정보 조회 진입")

        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
        }

        response = self.call_api(self.LIST_PERFORMANCES_ENDPOINT, params)
        return [Performance(**peformance) for peformance in response.json()]

#벌크 엔드포인트

    def get_bulk_player_file(self) -> bytes:
        """선수 데이터가 포함된 벌크 파일을 반환한다."""

        logger.debug("선수 벌크 파일 가져오기 진입")

        player_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["players"]

        response = httpx.get(player_file_path, follow_redirects=True)

        if response.status_code == 200:
            logger.debug("파일 다운로드 성공")
            return response.content

    def get_bulk_league_file(self) -> bytes:
        """리그 데이터가 포함된 CSV 파일을 반환한다."""

        logger.debug("리그 벌크 파일 가져오기 진입")

        league_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["leagues"]

        response = httpx.get(league_file_path, follow_redirects=True)

        if response.status_code == 200:
            logger.debug("파일 다운로드 성공")
            return response.content

    def get_bulk_performance_file(self) -> bytes:
        """성적 데이터가 포함된 CSV 파일을 반환한다."""

        logger.debug("성적 벌크 파일 가져오기 진입")

        performance_file_path = (
            self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["performances"]
        )

        response = httpx.get(performance_file_path, follow_redirects=True)

        if response.status_code == 200:
            logger.debug("파일 다운로드 성공")
            return response.content

    def get_bulk_team_file(self) -> bytes:
        """팀 데이터가 포함된 CSV 파일을 반환한다."""

        logger.debug("팀 벌크 파일 가져오기 진입")

        team_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["teams"]

        response = httpx.get(team_file_path, follow_redirects=True)

        if response.status_code == 200:
            logger.debug("파일 다운로드 성공")
            return response.content

    def get_bulk_team_player_file(self) -> bytes:
        """팀 선수 데이터가 포함된 CSV 파일을 반환한다."""

        logger.debug("팀 선수 벌크 파일 가져오기 진입")

        team_player_file_path = (
            self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["team_players"]
        )

        response = httpx.get(team_player_file_path, follow_redirects=True)

        if response.status_code == 200:
            logger.debug("파일 다운로드 성공")
            return response.content
