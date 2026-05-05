"""
Streamlit 로그인 인증 모듈
"""
import os
import streamlit as st
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def check_credentials(username: str, password: str) -> bool:
    """사용자 인증 확인"""
    env_username = os.getenv("ID", "admin")
    env_password = os.getenv("PW", "password123")
    
    return username == env_username and password == env_password

def login_form() -> bool:
    """로그인 폼 렌더링 및 인증 처리"""
    st.markdown("### 🔐 로그인")
    
    with st.form("login_form"):
        username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        submit_button = st.form_submit_button("로그인")
        
        if submit_button:
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("로그인 성공!")
                st.rerun()
                return True
            else:
                st.error("❌ 잘못된 사용자명 또는 비밀번호입니다.")
                return False
    
    return False

def logout():
    """로그아웃 처리"""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'username' in st.session_state:
        del st.session_state.username
    st.rerun()

def is_authenticated() -> bool:
    """인증 상태 확인"""
    return st.session_state.get('authenticated', False)

def require_auth(func):
    """인증이 필요한 함수를 위한 데코레이터"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("🔒 이 페이지에 접근하려면 로그인이 필요합니다.")
            login_form()
            return None
        return func(*args, **kwargs)
    return wrapper
