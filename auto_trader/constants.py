"""Constants for auto trader application."""
from typing import Dict, List
from pathlib import Path

# Market mappings by currency
MARKET_MAPPING: Dict[str, List[str]] = {
    'KRW': ['KRX', 'CRYPTO'],
    'USD': ['AMEX', 'NASDAQ', 'NYSE'],
}

# Default configuration values
DEFAULT_THRESHOLD = 0.1
DEFAULT_AMOUNT_LIMIT = int(1e7)

# Order timeout configurations (in seconds)
ORDER_CHECK_INTERVAL = 1
ORDER_PRICE_ADJUST_INTERVAL = 100
ORDER_TIMEOUT_LIMIT = 1000

# Price adjustment factors
PRICE_ADJUSTMENT_RATE_BUY = 1.001
PRICE_ADJUSTMENT_RATE_SELL = 0.999

# Minimum order amounts
MIN_ORDER_AMOUNT = 10000.0  # 10,000 KRW minimum order amount
MIN_CRYPTO_QUANTITY = 1e-6

# API endpoints
UPBIT_API_BASE_URL = "https://api.upbit.com"

# Tick size rules for KRW stocks
TICK_SIZE_RULES = [
    (1000, 1),  # Under 1,000 won: 1 won unit
    (5000, 5),  # 1,000 ~ 4,999 won: 5 won unit
    (10000, 10),  # 5,000 ~ 9,999 won: 10 won unit
    (50000, 50),  # 10,000 ~ 49,999 won: 50 won unit
    (100000, 100),  # 50,000 ~ 99,999 won: 100 won unit
    (500000, 500),  # 100,000 ~ 499,999 won: 500 won unit
    (float('inf'), 1000),  # 500,000 won and above: 1,000 won unit
]

# US stock tick sizes
USD_TICK_SIZE_HIGH = 0.01  # For stocks >= $1
USD_TICK_SIZE_LOW = 0.0001  # For stocks < $1
USD_PRICE_THRESHOLD = 1.0

# Slack configuration (should be moved to environment variables)
DEFAULT_SLACK_CHANNEL = "C02SGLQV529"
DEFAULT_USER_MENTION = "김대현"

# Resolve directories relative to this package's root to be robust across environments
_PACKAGE_ROOT = Path(__file__).resolve().parent
AUTH_DIR = str(_PACKAGE_ROOT / "auth")
CONFIG_DIR = str(_PACKAGE_ROOT / "config")