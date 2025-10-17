"""
자산 배분 설정 페이지
"""
import streamlit as st
from .config_utils import load_asset_allocate_config, save_asset_allocate_config
from .asset_utils import clear_asset_ratios_cache


def render_asset_allocation_page():
    """자산 배분 설정 페이지를 렌더링합니다."""
    st.header("자산 배분 설정 수정")
    st.write("AssetAllocateAgent.yaml 파일의 자산 배분 설정을 수정할 수 있습니다.")
    
    # 캐시 새로고침 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 새로고침", help="현재 자산 비율 데이터를 새로 조회합니다", type="secondary"):
            clear_asset_ratios_cache()
            st.success("캐시가 초기화되었습니다. 데이터를 새로 조회합니다.")
            st.rerun()
    with col2:
        st.caption("💡 자산 비율 데이터는 5분간 캐시됩니다. 최신 데이터가 필요하면 새로고침 버튼을 클릭하세요.")
    
    # 설정 파일 로드
    config = load_asset_allocate_config()
    
    if not config:
        st.error("설정 파일을 로드할 수 없습니다.")
        return
    
    # 계좌별 설정 편집
    for account_id, account_config in config.items():
        with st.expander(f"계좌: {account_id}", expanded=True):
            
            for currency, currency_config in account_config.items():
                st.subheader(f"{currency} 자산 설정")
                
                # Threshold 설정
                threshold = st.number_input(
                    f"{currency} Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=currency_config.get('threshold', 0.08),
                    step=0.01,
                    key=f"threshold_{account_id}_{currency}"
                )
                
                # 자산별 비율 설정
                st.write("**자산별 비율 설정:**")
                assets = currency_config.get('assets', {})
                
                # 자산 추가/삭제를 위한 세션 상태 초기화
                if f"assets_{account_id}_{currency}" not in st.session_state:
                    st.session_state[f"assets_{account_id}_{currency}"] = assets.copy()
                
                new_assets = st.session_state[f"assets_{account_id}_{currency}"]
                total_ratio = 0.0
                
                
                # 기존 자산들 표시
                assets_to_remove = []
                if new_assets:
                    for asset_code, ratio in new_assets.items():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"`{asset_code}`")
                        with col2:
                            new_ratio = st.number_input(
                                "목표 비율",
                                min_value=0.0,
                                max_value=1.0,
                                value=ratio,
                                step=0.01,
                                key=f"asset_{account_id}_{currency}_{asset_code}"
                            )
                            new_assets[asset_code] = new_ratio
                            total_ratio += new_ratio
                        with col3:
                            if st.button("🗑️", key=f"delete_{account_id}_{currency}_{asset_code}", help="자산 삭제", type="secondary"):
                                assets_to_remove.append(asset_code)
                else:
                    st.info("💡 아직 설정된 자산이 없습니다. 아래에서 새 자산을 추가해보세요.")
                
                # 삭제할 자산들 제거
                for asset_code in assets_to_remove:
                    del new_assets[asset_code]
                    st.session_state[f"assets_{account_id}_{currency}"] = new_assets
                    st.success(f"자산 '{asset_code}'이 삭제되었습니다!")
                    st.rerun()
                
                # 자산 추가 섹션
                st.markdown("---")
                with st.expander("➕ 새 자산 추가", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        new_asset_code = st.text_input(
                            "자산 코드",
                            placeholder="예: 379800, TSLL, PLTR",
                            key=f"new_asset_code_{account_id}_{currency}",
                            help="KRW 자산은 6자리 숫자, USD 자산은 영문 코드를 입력하세요"
                        )
                    
                    with col2:
                        new_asset_ratio = st.number_input(
                            "비율",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.0,
                            step=0.01,
                            key=f"new_asset_ratio_{account_id}_{currency}",
                            help="0.0 ~ 1.0 사이의 값 (예: 0.1 = 10%)"
                        )
                    
                    with col3:
                        st.write("")  # 공간 확보
                        st.write("")  # 공간 확보
                        if st.button("➕ 추가", key=f"add_asset_{account_id}_{currency}", type="primary"):
                            if new_asset_code and new_asset_code not in new_assets:
                                new_assets[new_asset_code] = new_asset_ratio
                                st.session_state[f"assets_{account_id}_{currency}"] = new_assets
                                st.success(f"자산 '{new_asset_code}' (비율: {new_asset_ratio:.1%})이 추가되었습니다!")
                                st.rerun()
                            elif new_asset_code in new_assets:
                                st.error("❌ 이미 존재하는 자산 코드입니다.")
                            else:
                                st.error("❌ 자산 코드를 입력해주세요.")
                
                # 총 비율 표시
                st.write(f"**총 비율: {total_ratio:.2f}**")
                if total_ratio > 1.0:
                    st.warning("⚠️ 총 비율이 100%를 초과했습니다!")
                elif total_ratio < 1.0:
                    st.info("💡 총 비율이 100% 미만입니다.")
                
                # 설정 업데이트
                config[account_id][currency]['threshold'] = threshold
                config[account_id][currency]['assets'] = new_assets
    
    # 저장 버튼
    if st.button("💾 설정 저장", type="primary", use_container_width=True):
        if save_asset_allocate_config(config):
            st.success("설정이 성공적으로 저장되었습니다!")
            st.rerun()
