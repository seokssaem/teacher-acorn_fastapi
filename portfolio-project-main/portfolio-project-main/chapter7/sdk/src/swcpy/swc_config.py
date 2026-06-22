import os
from dotenv import load_dotenv

load_dotenv()

class SWCConfig:
    """SWC SDK 클라이언트 초기화를 위한 인수를 관리하는 설정 클래스

    이 클래스는 API 호출을 위한 기본 URL, 오류 발생 시 재시도(backoff) 여부,
    재시도 최대 시간, 대용량 파일 처리 형식 등 주요 설정 인자를 포함한다.
    """

    swc_base_url: str
    swc_backoff: bool
    swc_backoff_max_time: int
    swc_bulk_file_format: str

    def __init__(
        self,
        swc_base_url: str = None,
        backoff: bool = True,
        backoff_max_time: int = 30,
        bulk_file_format: str = "csv",
    ):
        """설정 클래스 생성자
        
        이 생성자는 SWC SDK 클라이언트를 설정할 때 사용할 인자를 받아 내부 변수로 초기화된다. 
        인자가 전달되지 않으면 기본값 또는 환경 변수를 사용한다.

        인수:
        - swc_base_url (선택): 모든 API 호출에 사용할 기본 URL
                               직접 전달하거나 환경 변수(SWC_API_BASE_URL)로 지정 가능

        - backoff: 오류 발생 시 SDK가 백오프 전략으로 재시도할지 여부를 설정하는 부울 값

        - backoff_max_time: API 호출 재시도를 중단하기 전까지의 최대 시간(초 단위)

        - bulk_file_format: 대용량 데이터 파일 형식. 'csv' 또는 'parquet' 중 선택
        """

        self.swc_base_url = swc_base_url or os.getenv("SWC_API_BASE_URL")
        print(f"SWC_API_BASE_URL in SWCConfig init: {self.swc_base_url}")  


        if not self.swc_base_url:
            raise ValueError("기본 URL은 필수입니다. SWC_API_BASE_URL 환경 변수를 설정하세요.")

        self.swc_backoff = backoff
        self.swc_backoff_max_time = backoff_max_time
        self.swc_bulk_file_format = bulk_file_format

    def __str__(self):
        """설정 객체의 내용을 문자열로 반환하는 메서드

        이 메서드는 로깅이나 디버깅 시 설정 값을 출력하는 데 사용된다.
        명시적으로 정의하지 않으면 기본 문자열 표현이 사용되며, 정보가 부족할 수 있다.
        """
        return f"{self.swc_base_url} {self.swc_backoff} {self.swc_backoff_max_time}  {self.swc_bulk_file_format}"