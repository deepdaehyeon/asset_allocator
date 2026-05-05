"""
원달러 평균 매수 설정 페이지
"""
import streamlit as st
from .config_utils import load_cost_average_config, save_cost_average_config


def render_cost_average_page():
    """원달러 평균 매수 설정 페이지를 렌더링합니다."""
    st.header("원달러 평균 매수 설정")
    st.write("CostAverageAgent.yaml 파일의 원달러 평균 매수 설정을 수정할 수 있습니다.")
    
    # 설정 파일 로드
    config = load_cost_average_config()
    
    if not config:
        st.error("설정 파일을 로드할 수 없습니다.")
        return
    
    # 계좌별 설정 편집
    for account_id, account_config in config.items():
        with st.expander(f"계좌: {account_id}", expanded=True):
            
            for currency, currency_config in account_config.items():
                st.subheader(f"{currency} 자산 설정")
                
                # 자산별 금액 설정
                st.write("**자산별 매수 금액 설정:**")
                assets = currency_config
                
                # 자산 추가/삭제를 위한 세션 상태 초기화
                if f"cost_assets_{account_id}_{currency}" not in st.session_state:
                    st.session_state[f"cost_assets_{account_id}_{currency}"] = assets.copy()
                
                new_assets = st.session_state[f"cost_assets_{account_id}_{currency}"]
                total_amount = 0.0
                
                # 기존 자산들 표시
                assets_to_remove = []
                if new_assets:
                    for asset_code, amount_config in new_assets.items():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.write(f"`{asset_code}`")
                        with col2:
                            # amount 또는 qty 필드 처리
                            if isinstance(amount_config, dict):
                                amount_value = amount_config.get('amount', amount_config.get('qty', 0))
                            else:
                                amount_value = amount_config
                            
                            new_amount = st.number_input(
                                "매수 금액/수량",
                                min_value=0.0,
                                value=float(amount_value),
                                step=1000.0,
                                key=f"cost_asset_{account_id}_{currency}_{asset_code}"
                            )
                            new_assets[asset_code] = new_amount
                            total_amount += new_amount
                        with col3:
                            st.write("")  # 공간 확보
                        with col4:
                            if st.button("🗑️", key=f"cost_delete_{account_id}_{currency}_{asset_code}", help="자산 삭제", type="secondary"):
                                assets_to_remove.append(asset_code)
                else:
                    st.info("💡 아직 설정된 자산이 없습니다. 아래에서 새 자산을 추가해보세요.")
                
                # 삭제할 자산들 제거
                for asset_code in assets_to_remove:
                    del new_assets[asset_code]
                    st.session_state[f"cost_assets_{account_id}_{currency}"] = new_assets
                    st.success(f"자산 '{asset_code}'이 삭제되었습니다!")
                    st.rerun()
                
                # 자산 추가 섹션
                st.markdown("---")
                with st.expander("➕ 새 자산 추가", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        new_asset_code = st.text_input(
                            "자산 코드",
                            placeholder="예: BTC, ETH, TSLL, PLTR",
                            key=f"new_cost_asset_code_{account_id}_{currency}",
                            help="암호화폐는 영문 코드, 주식은 티커 심볼을 입력하세요"
                        )
                    
                    with col2:
                        new_asset_amount = st.number_input(
                            "매수 금액/수량",
                            min_value=0.0,
                            value=0.0,
                            step=1000.0,
                            key=f"new_cost_asset_amount_{account_id}_{currency}",
                            help="매수할 금액 또는 수량을 입력하세요"
                        )
                    
                    with col3:
                        st.write("")  # 공간 확보
                        st.write("")  # 공간 확보
                        if st.button("➕ 추가", key=f"add_cost_asset_{account_id}_{currency}", type="primary"):
                            if new_asset_code and new_asset_code not in new_assets:
                                new_assets[new_asset_code] = new_asset_amount
                                st.session_state[f"cost_assets_{account_id}_{currency}"] = new_assets
                                st.success(f"자산 '{new_asset_code}' (금액: {new_asset_amount:,.0f})이 추가되었습니다!")
                                st.rerun()
                            elif new_asset_code in new_assets:
                                st.error("❌ 이미 존재하는 자산 코드입니다.")
                            else:
                                st.error("❌ 자산 코드를 입력해주세요.")
                
                # 총 금액 표시
                st.write(f"**총 매수 금액: {total_amount:,.0f}**")
                
                # 설정 업데이트
                config[account_id][currency] = new_assets
    
    # 저장 버튼
    if st.button("💾 원달러 평균 매수 설정 저장", type="primary", use_container_width=True):
        if save_cost_average_config(config):
            st.success("원달러 평균 매수 설정이 성공적으로 저장되었습니다!")
            st.rerun()
