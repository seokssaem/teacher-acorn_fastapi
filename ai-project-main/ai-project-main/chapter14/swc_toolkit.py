import os
from typing import Optional, Type, List

from pydantic import BaseModel, Field

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, BaseToolkit

try:
            from swcpy import SWCClient
            from swcpy import SWCConfig
            from swcpy.swc_client import League, Team
except ImportError:
    raise ImportError(
        "swcpy가 설치돼 있지 않습니다. 설치 후 진행하세요."
    )

config = SWCConfig(backoff=False)
local_swc_client = SWCClient(config)


class HealthCheckInput(BaseModel):
    pass

class HealthCheckTool(BaseTool):
    name: str = "HealthCheck"
    description: str = (
            "다른 API 호출 전에 API가 정상적으로 동작하는지 확인할 때 사용합니다."
    )
    args_schema: Type[HealthCheckInput] = HealthCheckInput
    return_direct: bool = False

    def _run(
        self, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """API의 상태를 확인합니다."""
        health_check_response = local_swc_client.get_health_check()
        return health_check_response.text
    

class LeaguesInput(BaseModel):
    league_name: Optional[str] = Field(
         default=None, 
         description="리그 이름입니다. 전체 리그를 조회하려면 비워 두거나 None으로 설정하세요.")

class ListLeaguesTool(BaseTool):
    name: str = "ListLeagues"
    description: str = (
        "SportsWorldCentral에서 리그 정보를 조회합니다."
        "리그에 팀이 있는 경우 함께 반환됩니다."
    )
    args_schema: Type[LeaguesInput] = LeaguesInput
    return_direct: bool = False

    def _run(
        self, league_name: Optional[str] = None, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> List[League]:
        """SportsWorldCentral에서 리그 정보를 가져옵니다."""
        # 리그 이름으로 API를 호출한다. None도 가능하다.
        list_leagues_response = local_swc_client.list_leagues(league_name=league_name)
        return list_leagues_response

class TeamsInput(BaseModel):
    team_name: Optional[str] = Field(
         default=None, 
         description="조회할 팀 이름입니다. 전체 팀을 조회하려면 비워 두거나 None으로 두세요.")
    league_id: Optional[int] = Field(
         default=None, 
         description=(
              "리그의 ID(숫자)입니다. 전체 리그의 팀을 조회하려면 비워 두세요."
              ))

class ListTeamsTool(BaseTool):
    name: str = "ListTeams"
    description: str = (
         "SportsWorldCentral에서 팀 목록을 조회합니다."
         "팀 내에 선수가 있는 경우 함께 반환됩니다."
         "특정 리그의 팀만 조회하려면 리그 ID를 입력할 수 있습니다.")
    args_schema: Type[TeamsInput] = TeamsInput
    return_direct: bool = False

    def _run(
        self, team_name: Optional[str] = None, 
        league_id: Optional[int] = None, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> List[Team]:
        """SportsWorldCentral에서 팀 목록을 조회합니다."""
        list_teams_response = local_swc_client.list_teams(
             team_name=team_name, league_id= league_id)
        return list_teams_response


class SportsWorldCentralToolkit(BaseToolkit):
    def get_tools(self) -> List[BaseTool]:
        """툴킷에 포함된 도구 목록을 반환합니다."""
        return [HealthCheckTool(), ListLeaguesTool(), ListTeamsTool()]

