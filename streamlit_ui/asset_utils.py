"""
자산 비율 조회 유틸리티
"""
import streamlit as st
import yaml
from pathlib import Path
from typing import Dict, Any
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextlib import contextmanager

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from run import create_account
from auto_trader.constants import MARKET_MAPPING


def run_with_timeout(func, timeout_seconds, *args, **kwargs):
    """함수를 타임아웃과 함께 실행합니다."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError:
            raise TimeoutError(f"작업이 {timeout_seconds}초 내에 완료되지 않았습니다.")


@st.cache_data(ttl=300)  # 5분 캐시
def get_current_asset_ratios() -> Dict[str, Dict[str, Dict[str, float]]]:
    """실제 계좌에서 현재 자산 비율을 가져옵니다."""
    # 일단 샘플 데이터를 사용하도록 임시 변경
    # 실제 API 호출은 시간이 오래 걸리고 안정성 문제가 있을 수 있음
    try:
        # 인증 설정 로드
        auth_path = Path("auto_trader/config/auth.yaml")
        if not auth_path.exists():
            st.warning("인증 설정 파일이 없습니다. 샘플 데이터를 사용합니다.")
            return get_sample_asset_ratios()
        
        with open(auth_path, 'r', encoding='utf-8') as f:
            auth_config = yaml.safe_load(f)
        
        # 설정 파일에서 계좌 목록 가져오기
        from .config_utils import load_asset_allocate_config
        config = load_asset_allocate_config()
        if not config:
            return get_sample_asset_ratios()
        
        current_ratios = {}
        
        for account_id in config.keys():
            if account_id not in auth_config:
                st.info(f"계좌 {account_id}의 인증 정보가 없습니다. 건너뜁니다.")
                continue
                
            try:
                st.info(f"계좌 {account_id} 조회 중...")
                
                # 계좌 생성
                account = create_account(account_id, auth_config)
                if not account:
                    st.warning(f"계좌 {account_id} 생성 실패")
                    continue
                
                st.info(f"계좌 {account_id} 잔고 조회 중...")
                
                # 잔고 조회 (30초 타임아웃 적용)
                try:
                    balance = run_with_timeout(account.get_balance, 30)
                except TimeoutError as e:
                    st.error(f"계좌 {account_id} 잔고 조회 타임아웃: {e}")
                    continue
                current_ratios[account_id] = {}
                
                st.info(f"계좌 {account_id} 자산 비율 계산 중...")
                
                # 각 통화별로 자산 비율 계산
                for currency in balance.deposits.keys():
                    if currency not in config[account_id]:
                        continue
                    
                    # 현재 자산 금액 계산
                    amt = {}
                    currency_markets = MARKET_MAPPING.get(currency, [])
                    
                    # 주식 자산
                    for stock in balance.stocks:
                        if stock.market in currency_markets:
                            amt[stock.symbol] = float(stock.amount)
                    
                    # 현금 (10초 타임아웃 적용)
                    try:
                        cash_amount = run_with_timeout(account.get_cash, 10, currency)
                        amt['cash'] = cash_amount
                    except TimeoutError as timeout_error:
                        st.warning(f"계좌 {account_id} {currency} 현금 조회 타임아웃: {timeout_error}")
                        amt['cash'] = 0.0
                    except Exception as cash_error:
                        st.warning(f"계좌 {account_id} {currency} 현금 조회 실패: {cash_error}")
                        amt['cash'] = 0.0
                    
                    # 총 금액
                    amt_total = sum(amt.values())
                    
                    if amt_total > 0:
                        # 비율 계산
                        ratios = {}
                        for asset_code, amount in amt.items():
                            ratios[asset_code] = amount / amt_total
                        
                        current_ratios[account_id][currency] = ratios
                        st.success(f"계좌 {account_id} {currency} 자산 비율 계산 완료")
                    else:
                        st.warning(f"계좌 {account_id} {currency} 총 자산이 0입니다")
                
            except Exception as e:
                st.error(f"계좌 {account_id} 조회 중 오류: {e}")
                continue
        
        if not current_ratios:
            st.warning("조회된 계좌 데이터가 없습니다. 샘플 데이터를 사용합니다.")
            return get_sample_asset_ratios()
        
        return current_ratios
        
    except Exception as e:
        st.error(f"현재 자산 비율 조회 중 오류: {e}")
        return get_sample_asset_ratios()


def clear_asset_ratios_cache():
    """자산 비율 캐시를 무효화합니다."""
    get_current_asset_ratios.clear()


def get_sample_asset_ratios() -> Dict[str, Dict[str, Dict[str, float]]]:
    """샘플 자산 비율 데이터를 반환합니다."""
    return {
        "64378890-01": {
            "KRW": {
                "379800": 0.25,  # kodex s&p 500
                "379810": 0.30,  # kodex 나스닥 100
                "305080": 0.12,  # tiger 미국채 10년
                "468630": 0.08,  # kodex 미국 회사채
                "469830": 0.10,  # sol 초단기채권
                "411060": 0.15,  # ace krx 금 현물
            },
            "USD": {
                "TSLL": 0.05,
                "TSLY": 0.05,
                "PLTR": 0.20,
                "SHY": 0.10,
                "IEF": 0.10,
                "TLT": 0.10,
                "IAU": 0.15,
            }
        },
        "64521213-01": {
            "KRW": {
                "379800": 0.28,  # kodex s&p 500
                "379810": 0.31,  # kodex 나스닥 100
                "305080": 0.09,  # tiger 미국채 10년
                "468630": 0.11,  # kodex 회사채
                "469830": 0.09,  # sol 초단기채권
                "411060": 0.12,  # ace krx 금 현물
            }
        }
    }
