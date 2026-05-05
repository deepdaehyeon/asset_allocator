"""
설정 파일 로드/저장 유틸리티
"""
import yaml
import streamlit as st
from pathlib import Path
from typing import Dict, Any


# 설정 파일 경로
ASSET_ALLOCATE_CONFIG_FILE = Path("auto_trader/config/AssetAllocateAgent.yaml")
COST_AVERAGE_CONFIG_FILE = Path("auto_trader/config/CostAverageAgent.yaml")


def load_asset_allocate_config() -> Dict[str, Any]:
    """AssetAllocateAgent.yaml 파일을 로드합니다."""
    try:
        with open(ASSET_ALLOCATE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error(f"설정 파일을 찾을 수 없습니다: {ASSET_ALLOCATE_CONFIG_FILE}")
        return {}
    except yaml.YAMLError as e:
        st.error(f"YAML 파일 오류: {e}")
        return {}


def save_asset_allocate_config(config: Dict[str, Any]) -> bool:
    """AssetAllocateAgent.yaml 파일을 저장합니다."""
    try:
        with open(ASSET_ALLOCATE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"설정 파일 저장 오류: {e}")
        return False


def load_cost_average_config() -> Dict[str, Any]:
    """CostAverageAgent.yaml 파일을 로드합니다."""
    try:
        with open(COST_AVERAGE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error(f"설정 파일을 찾을 수 없습니다: {COST_AVERAGE_CONFIG_FILE}")
        return {}
    except yaml.YAMLError as e:
        st.error(f"YAML 파일 오류: {e}")
        return {}


def save_cost_average_config(config: Dict[str, Any]) -> bool:
    """CostAverageAgent.yaml 파일을 저장합니다."""
    try:
        with open(COST_AVERAGE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"설정 파일 저장 오류: {e}")
        return False
