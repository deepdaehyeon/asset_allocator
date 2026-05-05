"""
리밸런싱 실행 페이지
"""
import streamlit as st
from .rebalancing_utils import run_rebalancing


def render_rebalancing_page():
    """리밸런싱 실행 페이지를 렌더링합니다."""
    st.header("리밸런싱 실행")
    st.write("자산 배분을 목표 비율로 조정하는 리밸런싱을 실행합니다.")
    
    # 경고 메시지
    st.warning("⚠️ 리밸런싱 실행 시 실제 거래가 발생할 수 있습니다. 신중하게 실행해주세요.")
    
    # 리밸런싱 정보 표시
    st.info("""
    **리밸런싱 실행 내용:**
    - `python run.py -aaa` 명령어 실행
    - AssetAllocateAgent가 설정된 비율에 따라 자동으로 매매 주문 실행
    - 각 계좌별로 KRW, USD 자산을 목표 비율로 조정
    """)
    
    # 실행 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 리밸런싱 실행", type="primary", use_container_width=True):
            with st.spinner("리밸런싱을 실행 중입니다..."):
                run_rebalancing()
