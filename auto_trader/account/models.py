from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Stock:
    """Stock holding information."""

    symbol: str
    amount: float
    market: str
    profit: float = 0.0


@dataclass
class Balance:
    """Account balance information."""

    deposits: Dict[str, float]
    stocks: List[Stock]
    account_number: Optional[str] = None
