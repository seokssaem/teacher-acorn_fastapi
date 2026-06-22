import backoff
import logging
import httpx

HEALTH_CHECK_ENDPOINT = "/"
LIST_LEAGUES_ENDPOINT = "/v0/leagues/"
LIST_PLAYERS_ENDPOINT = "/v0/players/"
LIST_PERFORMANCES_ENDPOINT = "/v0/performances/"
LIST_TEAMS_ENDPOINT = "/v0/teams/"
LIST_WEEKS_ENDPOINT = "/v0/weeks/"
GET_COUNTS_ENDPOINT = "/v0/counts/"

logger = logging.getLogger(__name__) 

@backoff.on_exception(
    wait_gen=backoff.expo, 
    exception=(httpx.RequestError, httpx.HTTPStatusError),  
    max_time=5,  
    jitter=backoff.random_jitter  
)
def call_api_endpoint(
    base_url: str,
    api_endpoint: str, 
    api_params: dict = None
) -> httpx.Response:

    try:
        with httpx.Client(base_url=base_url) as client: 
            logger.debug(f"base_url: {base_url}, api_endpoint: {api_endpoint}")
            response = client.get(api_endpoint, params=api_params)
            response.raise_for_status()
            logger.debug(f"API 응답 수신 완료: {response.json()}")
            return response
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 상태 오류 발생: {e.response.text}")
        return httpx.Response(status_code=e.response.status_code, 
                              content=b"API error")
    except httpx.RequestError as e:
        logger.error(f"응답 오류 발생: {str(e)}")
        return httpx.Response(status_code=500, content=b"Network error")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        return httpx.Response(status_code=500, content=b"Unexpected error")