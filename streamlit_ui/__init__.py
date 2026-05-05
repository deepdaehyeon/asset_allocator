"""
Asset Allocation Manager Streamlit App

이 패키지는 자산 배분 관리를 위한 Streamlit 웹 애플리케이션을 제공합니다.

주요 기능:
- 자산 배분 설정 관리
- 원달러 평균 매수 설정 관리  
- 리밸런싱 실행

사용법:
    from streamlit.main import main
    main()
"""

__version__ = "1.0.0"
__author__ = "Asset Allocation Team"

from .asset_allocation_page import render_asset_allocation_page
from .cost_average_page import render_cost_average_page
from .rebalancing_page import render_rebalancing_page
from .auth import login_form, logout, is_authenticated, require_auth
