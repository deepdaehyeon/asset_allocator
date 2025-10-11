"""
리밸런싱 실행 유틸리티
"""
import streamlit as st
import subprocess
import os


def run_rebalancing():
    """리밸런싱을 실행합니다 (python run.py -aaa -f)."""
    try:
        # 현재 디렉토리에서 python run.py -aaa --forced 실행
        result = subprocess.run(
            ["python", "run.py", "-aaa", "--forced"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            st.success("리밸런싱이 성공적으로 실행되었습니다!")
            if result.stdout:
                st.text("실행 결과:")
                st.text(result.stdout)
        else:
            st.error(f"리밸런싱 실행 중 오류가 발생했습니다: {result.stderr}")
            
    except Exception as e:
        st.error(f"리밸런싱 실행 오류: {e}")
