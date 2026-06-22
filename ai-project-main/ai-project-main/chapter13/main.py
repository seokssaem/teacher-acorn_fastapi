"""Fantasy 선수 영입 API"""

from fastapi import FastAPI
import onnxruntime as rt
import numpy as np
from schemas import FantasyAcquisitionFeatures, PredictionOutput

api_description = """
이 API는 판타지 풋볼에서 선수를 영입하는 데 필요한 비용을 산출합니다.
엔드포인트는 다음과 같이 구성되어 있습니다.

## 분석
API의 상태 정보를 제공합니다.

## 예상 비용 계산
선수 영입 예상 비용을 계산합니다.
"""



# ONNX 모델 불러오기
sess_10 = rt.InferenceSession("acquisition_model_10.onnx", 
                              providers=["CPUExecutionProvider"])
sess_50 = rt.InferenceSession("acquisition_model_50.onnx", 
                              providers=["CPUExecutionProvider"])
sess_90 = rt.InferenceSession("acquisition_model_90.onnx", 
                              providers=["CPUExecutionProvider"])

# 모델별 입력 및 출력 이름 추출
input_name_10 = sess_10.get_inputs()[0].name
label_name_10 = sess_10.get_outputs()[0].name
input_name_50 = sess_50.get_inputs()[0].name
label_name_50 = sess_50.get_outputs()[0].name
input_name_90 = sess_90.get_inputs()[0].name
label_name_90 = sess_90.get_outputs()[0].name

# OpenAPI 명세에 필요한 추가 정보와 함께 FastAPI 애플리케이션 객체를 초기화한다.
app = FastAPI(
    description=api_description,
    title="Fantasy 선수 영입 API",
    version="0.1",
)

@app.get(
    "/",
    summary="Fantasy 선수 영입 API의 상태를 확인합니다.",
    description="""이 엔드포인트를 사용해 API가 실행 중인지 확인합니다. 
    다른 엔드포인트를 호출하기 전에 먼저 호출해 API의 상태를 확인할 수 있습니다.""",
    response_description="메시지가 포함된 JSON 응답입니다. API가 실행 중이면 메시지가 '성공(successful)'이라고 표시됩니다.",
    operation_id="v0_health_check",
    tags=["분석"],
)
def root():
    return {"message": "API 상태 확인 성공"}


# 예측 경로 정의
@app.post("/predict/", 
          response_model=PredictionOutput,
          summary="선수 영입 예상 비용을 계산합니다.",
          description="""이 엔드포인트를 사용해 판타지 풋볼 선수를 영입하는 데 드는 비용 범위를 계산합니다.""",
          response_description="""각 백분위수별 예상 영입 금액이 포함된 JSON 레코드를 반환합니다.
          이들은 함께 선수 영입 비용의 가능한 범위를 제공합니다.""",
          operation_id="v0_predict",
          tags=["예상 비용 계산"],
)
def predict(features: FantasyAcquisitionFeatures):
    # Pydantic 모델을 NumPy 배열로 변환
    input_data = np.array([[features.waiver_value_tier, 
                            features.fantasy_regular_season_weeks_remaining, 
                            features.league_budget_pct_remaining]], 
                            dtype=np.int64)

    # ONNX 추론 실행
    pred_onx_10 = sess_10.run([label_name_10], {input_name_10: input_data})[0]
    pred_onx_50 = sess_50.run([label_name_50], {input_name_50: input_data})[0]
    pred_onx_90 = sess_90.run([label_name_90], {input_name_90: input_data})[0]


    # 예측을 Pydantic 응답 모델로 반환
    return PredictionOutput(winning_bid_10th_percentile=round(pred_onx_10.item(0), 2),
                            winning_bid_50th_percentile=round(pred_onx_50.item(0), 2),
                            winning_bid_90th_percentile=round(pred_onx_90.item(0), 2))
