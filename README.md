# AssetAllocation

## Description
Asset allocation system for trading operations with Streamlit web interface.

## Features
- 🔐 **로그인 시스템**: 환경변수 기반 사용자 인증
- 🔧 **자산 배분 설정**: 포트폴리오 자산 배분 관리
- 💰 **원달러 평균 매수**: 원달러 평균 매수 전략 설정
- ⚡ **리밸런싱**: 자동 리밸런싱 실행

## Setup

### 1. 환경변수 설정
`.env` 파일에 로그인 정보를 설정하세요:
```bash
STREAMLIT_USERNAME=admin
STREAMLIT_PASSWORD=password123
```

### 2. 가상환경 활성화
```bash
source .venv/bin/activate
```

### 3. Streamlit 앱 실행
```bash
streamlit run streamlit_app_new.py
```

## Login
- 기본 사용자명: `admin`
- 기본 비밀번호: `password123`
- 환경변수에서 변경 가능

## TODO
- 중복 오더 방지

## TMUX background running
tmux new-session -d -s streamlit 'source .venv/bin/activate && streamlit run streamlit_app_new.py --server.port 8501 --server.address 0.0.0.0'
tmux attach-session -t streamlit