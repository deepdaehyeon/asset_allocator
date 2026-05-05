"""
자산 비율 조회 유틸리티
"""
import streamlit as st
from pathlib import Path
import os
import yaml
from typing import Dict
import sys
import threading

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from run import create_account
from auto_trader.constants import MARKET_MAPPING, AUTH_DIR

# 전역 락
_account_lock = threading.Lock()

@st.cache_resource  # cache_data가 아닌 cache_resource 사용!
def get_kis_accounts(auth_config: dict) -> dict:
    """KIS 계좌 객체들을 싱글톤으로 관리 (thread-safe)"""
    print("🔧 KIS 계좌 객체 생성 중...", file=sys.stderr, flush=True)
    accounts = {}
    
    for account_id, credentials in auth_config.items():
        try:
            # 계좌 생성 (한 번만)
            account = create_account(account_id, credentials)
            if account:
                accounts[account_id] = account
                print(f"✅ 계좌 {account_id} 생성 완료", file=sys.stderr)
        except Exception as e:
            print(f"❌ 계좌 {account_id} 생성 실패: {e}", file=sys.stderr)
    
    return accounts


def get_current_asset_ratios() -> Dict[str, Dict[str, Dict[str, float]]]:
    """실제 계좌에서 현재 자산 비율을 가져옵니다."""
    try:
        # 인증 설정 로드
        auth_path = Path(os.path.join(AUTH_DIR, "keys.yaml"))
        if not auth_path.exists():
            print("⚠️ 인증 설정 파일이 없습니다.", file=sys.stderr)
            return get_sample_asset_ratios()
        
        with open(auth_path, 'r', encoding='utf-8') as f:
            auth_config = yaml.safe_load(f)
        
        # 설정 파일에서 계좌 목록 가져오기
        from .config_utils import load_asset_allocate_config
        config = load_asset_allocate_config()
        # 싱글톤 계좌 객체 가져오기 (캐시됨)
        accounts = get_kis_accounts(auth_config)
        current_ratios = {}
        
        for account_id in config.keys():
            if account_id not in accounts:
                print(f"⚠️ 계좌 {account_id} 객체 없음", file=sys.stderr)
                continue
            
            account = accounts[account_id]
            
            try:
                print(f"🔍 계좌 {account_id} 조회 시작", file=sys.stderr, flush=True)
                
                # 전역 락으로 한 번에 하나씩만 API 호출
                with _account_lock:
                    print(f"💰 계좌 {account_id} 잔고 조회 중...", file=sys.stderr, flush=True)
                    
                    # 타임아웃 적용
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("잔고 조회 30초 초과")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)
                    
                    try:
                        balance = account.get_balance()
                        signal.alarm(0)
                    except TimeoutError:
                        print(f"❌ 계좌 {account_id} 타임아웃", file=sys.stderr)
                        signal.alarm(0)
                        continue
                    finally:
                        signal.signal(signal.SIGALRM, signal.SIG_DFL)
                
                print(f"✅ 계좌 {account_id} 잔고 수신", file=sys.stderr, flush=True)
                
                current_ratios[account_id] = {}
                
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
                    
                    # 현금
                    with _account_lock:
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(10)
                        try:
                            cash_amount = account.get_cash(currency)
                            amt['cash'] = cash_amount
                            signal.alarm(0)
                        except TimeoutError:
                            print(f"⚠️ {account_id} {currency} 현금 조회 타임아웃", file=sys.stderr)
                            amt['cash'] = 0.0
                            signal.alarm(0)
                        except Exception as e:
                            print(f"⚠️ {account_id} {currency} 현금 조회 실패: {e}", file=sys.stderr)
                            amt['cash'] = 0.0
                        finally:
                            signal.signal(signal.SIGALRM, signal.SIG_DFL)
                    
                    # 총 금액
                    amt_total = sum(amt.values())
                    
                    if amt_total > 0:
                        # 비율 계산
                        ratios = {}
                        for asset_code, amount in amt.items():
                            ratios[asset_code] = amount / amt_total
                        
                        current_ratios[account_id][currency] = ratios
                        print(f"✅ {account_id} {currency} 완료", file=sys.stderr)
                    else:
                        print(f"⚠️ {account_id} {currency} 자산 없음", file=sys.stderr)
                
            except Exception as e:
                print(f"❌ 계좌 {account_id} 오류: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                continue
        
        if not current_ratios:
            print("⚠️ 조회된 데이터 없음. 샘플 사용", file=sys.stderr)
            return get_sample_asset_ratios()
        
        return current_ratios
        
    except Exception as e:
        print(f"❌ 전체 오류: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return get_sample_asset_ratios()

#
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
