
# 소프트웨어 개발 키트 (SDK)

이 SDK는 [AI와 데이터 사이언스 API](https://handsonapibook.com) 도서에서 제공하는 SportsWorldCentral Football API와 상호 작용하기 위한 파이썬 기반 SDK입니다.

## swcpy 설치 방법

이 SDK를 사용자 환경에 설치하려면 다음 명령어를 실행합니다.

`pip install swcpy@git+https://github.com/{사용자 이름}/portfolio-project#subdirectory=sdk`

## 사용 예제

이 SDK는 SWC API의 모든 엔드포인트를 구현하며, SWC 판타지 데이터를 CSV 형식으로 대용량 다운로드할 수 있는 기능도 제공합니다.

### API 기본 URL 설정

SDK는 환경 변수에서 `SWC_API_BASE_URL` 값을 참조합니다. 가장 권장하는 방식은 프로젝트 디렉터리에 `.env` 파일을 생성하고 다음 값을 포함시키는 것입니다.

```
SWC_API_BASE_URL={URL of your API}
```

또는 환경 변수로 직접 설정하거나, `SWCConfig()` 메서드에 인자로 전달할 수도 있습니다.

### 일반 API 함수 예시

일반 API 엔드포인트에 대한 SDK 함수를 호출하는 예시는 다음과 같습니다.


```python
from swcpy import SWCClient
from swcpy import SWCConfig

config = SWCConfig(swc_base_url="http://0.0.0.0:8000",backoff=False)
client = SWCClient(config)    
leagues_response = client.list_leagues()
print(leagues_response)
```

### 대용량 데이터 다운로드 예시

대용량 데이터 엔드포인트는 바이트 객체를 반환합니다.
다음은 대용량 파일 엔드포인트에서 파일을 로컬에 저장하는 예제 코드입니다.


```python
import csv
import os
from io import StringIO

config = SWCConfig()
    client = SWCClient(config)    

    """SDK를 통한 선수 데이터 다운로드 테스트"""
    player_file = client.get_bulk_player_file()


    # 파일 다운로드 확인을 위해 디스크에 파일 쓰기
    output_file_path = data_dir + 'players_file.csv'
    with open(output_file_path, 'wb') as f:
        f.write(player_file)
```
