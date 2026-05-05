from typing import List, Tuple

from auto_trader.constants import MARKET_MAPPING

from .base import BaseAgent

# Deprecated
class LeverageSwingAgent(BaseAgent):
    """Leverage swing agent class.

    [Config example]
    "$acc_no":
        "USD":
            "QLD":
                "qty": 1
                "max_qty": 80
                "profit_target": 0.1
    """

    name: str = "LeverageSwingAgent"

    def run(self) -> None:
        """Leverage swing buy till max quantity.

        Buy qty during positive profit, and buy double qty during negative profit.
        Sell when profit is larger than target profit.
        """
        pass