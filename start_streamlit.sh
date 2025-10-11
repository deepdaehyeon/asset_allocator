#!/bin/bash

# Streamlit 앱 시작 스크립트

echo "🚀 Asset Allocation Dashboard 시작 중..."

# 가상환경 활성화
export PATH="/root/.local/bin:$PATH"
source .venv/bin/activate

# 환경변수 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다. env_example.txt를 참고하여 .env 파일을 생성해주세요."
    exit 1
fi

# Streamlit 앱 실행
echo "📊 Streamlit 앱을 시작합니다..."
echo "🌐 외부 접근: http://YOUR_SERVER_IP:8501"
echo "🔐 로그인 정보: .env 파일에서 확인하세요"
echo "⏹️  중지하려면 Ctrl+C를 누르세요"
echo ""

streamlit run streamlit_app_new.py --server.port 8501 --server.address 0.0.0.0
