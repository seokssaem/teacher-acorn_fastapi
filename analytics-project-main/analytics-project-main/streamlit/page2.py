import streamlit as st
import pandas as pd
import logging
import nfl_data_py as nfl
# import matplotlib.pyplot as plt
import plotly.express as px  # 인터랙티브 시각화를 위해 plotly로 시각화

logger = logging.getLogger(__name__) 

st.header("SportsWorldCentral 데이터 앱")
st.subheader("팀 터치다운 통계")

try:
    flat_team_df_ordered = st.session_state['flat_team_df_ordered']
    unique_leagues = st.session_state['unique_leagues']
    selected_league = st.sidebar.selectbox('리그 ID 선택', unique_leagues)

    st.sidebar.divider()
    st.sidebar.subheader(":blue[데이터 출처]")
    st.sidebar.text("SportsWorldCentral")
    st.sidebar.text("NFLDataPy")

    # 선택한 리그로 필터링
    flat_team_df_ordered['league_id'] = flat_team_df_ordered['league_id'].astype(str)
    flat_team_df_ordered = flat_team_df_ordered[
        flat_team_df_ordered['league_id'] == selected_league
    ]

    # 2023 시즌 데이터 불러오기
    nfl_data_2023_df = nfl.import_seasonal_data([2023], 'REG')
    columns_to_select = ['player_id', 'passing_tds', 'rushing_tds', 'receiving_tds']
    nfl_data_2023_subset_df = nfl_data_2023_df[columns_to_select].copy()

    # 총 터치다운 계산
    nfl_data_2023_subset_df['total_tds'] = (
        nfl_data_2023_subset_df['passing_tds'] + 
        nfl_data_2023_subset_df['rushing_tds'] + 
        nfl_data_2023_subset_df['receiving_tds']
    )

    # SWC 팀 데이터와 NFL 데이터 병합
    merged_df = pd.merge(
        flat_team_df_ordered,
        nfl_data_2023_subset_df,
        how='left',
        left_on='gsis_id',
        right_on='player_id'
    )

    # 팀별 총 터치다운 합계 계산
    grouped_df = merged_df.groupby('team_name')['total_tds'].sum().reset_index()
    grouped_df = grouped_df.sort_values('total_tds', ascending=True)  # 가로 막대그래프를 위해 오름차순 정렬

    # Plotly로 가로 막대그래프 그리기
    fig = px.bar(
        grouped_df,
        x='total_tds',
        y='team_name',
        orientation='h',  # 가로 막대
        title="2023년 팀별 총 터치다운 수",
        labels={'total_tds': '총 터치다운 수', 'team_name': '팀 이름'},
        color='total_tds',
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        height=max(400, len(grouped_df) * 30),  # 팀 수가 많으면 높이 자동 조절
        xaxis_title="총 터치다운 수",
        yaxis_title="팀 이름"
    )

    # Streamlit에 plotly 그래프 표시
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    logger.error(f"예기치 않은 오류 발생: {str(e)}")
    st.write(f"예기치 않은 오류가 발생했습니다: {str(e)}")
