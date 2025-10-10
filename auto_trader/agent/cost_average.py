from typing import List, Optional, Tuple

from auto_trader.constants import MARKET_MAPPING
from auto_trader.utils import handle_exceptions

from .base import BaseAgent


class CostAverageAgent(BaseAgent):
    """Cost average buy agent class.

    [Config example]
    "$acc_no":
        "USD":
            "TSLY":
                "qty": 1
                "max_qty": 40 (optional)
                "amount": 1000 (optional, alternative to qty)
    """

    name: str = "CostAverageAgent"

    @handle_exceptions(reraise=True)
    def run(self) -> None:
        """Cost average buy till max quantity."""
        order_queue = self._build_order_queue()
        self._execute_order_queue(order_queue)

    def _build_order_queue(
        self,
    ) -> List[Tuple[str, Optional[int], Optional[float], str]]:
        """Build queue of orders to execute."""
        queue = []

        for currency in self.config.keys():
            for ticker, info in self.config[currency].items():
                # Check max quantity constraint
                if self._should_skip_due_to_max_qty(ticker, info):
                    continue

                # Extract order parameters
                amount = info.get("amount")
                qty = info.get("qty")

                if amount is None and qty is None:
                    self.send_msg(f"Warning: No qty or amount specified for {ticker}")
                    continue

                queue.append((ticker, qty, amount, currency))

        # Sort queue (sells before buys based on qty sign)
        queue.sort(key=lambda x: x[1] if x[1] is not None else 0)
        return queue

    def _should_skip_due_to_max_qty(self, ticker: str, info: dict) -> bool:
        """Check if ticker should be skipped due to max quantity constraint."""
        if 'max_qty' in info:
            if self.acnt.check_max_qty(ticker, info['max_qty']):
                return True
        return False

    def _execute_order_queue(
        self,
        queue: List[Tuple[str, Optional[int], Optional[float], str]],
    ) -> None:
        """Execute all orders in the queue."""
        self.send_msg(f"Executing {len(queue)} cost average orders")

        for ticker, qty, amount, currency in queue:
            try:
                self.order(ticker=ticker, qty=qty, amount=amount, currency=currency)
            except Exception as e:
                self.send_msg(f"Order failed for {ticker}: {str(e)}")
                continue
