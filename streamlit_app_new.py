"""
Asset Allocation Manager - 새로운 모듈화된 버전
"""
import streamlit as st
from pathlib import Path
import sys
from dotenv import load_dotenv

from streamlit_ui import render_asset_allocation_page, render_cost_average_page,  render_rebalancing_page
from streamlit_ui.auth import login_form, logout, is_authenticated
# 환경변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

# 페이지 설정
st.set_page_config(
    page_title="Asset Allocation Manager",
    page_icon="📊",
    layout="wide"
)

def main():
    """메인 앱 함수"""
    # 로그인 상태 확인
    if not is_authenticated():
        st.title("📊 Asset Allocation Manager")
        st.markdown("---")
        login_form()
        return
    
    # 로그인된 사용자용 메인 페이지
    st.title("📊 Asset Allocation Manager")
    
    # 로그아웃 버튼을 상단에 배치
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚪 로그아웃"):
            logout()
            return
    
    with col2:
        st.write(f"환영합니다, **{st.session_state.username}**님!")
    
    st.markdown("---")
    
    # 3개의 주요 기능을 탭으로 구성
    tab1, tab2, tab3 = st.tabs(["🔧 자산 배분 설정", "💰 원달러 평균 매수 설정", "⚡ 리밸런싱"])
    
    with tab1:
        render_asset_allocation_page()
    
    with tab2:
        render_cost_average_page()
    
    with tab3:
        render_rebalancing_page()


if __name__ == "__main__":
    main()