from typing import List, Tuple

from auto_trader.constants import MARKET_MAPPING
from auto_trader.utils import handle_exceptions

from .base import BaseAgent


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

    @handle_exceptions(reraise=True)
    def run(self) -> None:
        """Leverage swing buy till max quantity.

        Buy qty during positive profit, and buy double qty during negative profit.
        Sell when profit is larger than target profit.
        """
        balance = self.get_balance()
        order_queue = self._build_leverage_order_queue(balance)
        self._execute_order_queue(order_queue)

    def _build_leverage_order_queue(self, balance) -> List[Tuple[str, int, str]]:
        """Build queue of leverage-based orders."""
        queue = []

        for currency in self.config.keys():
            for ticker, info in self.config[currency].items():
                # Calculate order quantity based on current profit
                qty = self._calculate_leverage_qty(ticker, info, balance)

                if qty == 0:
                    continue

                # Check max quantity constraint
                if self._should_skip_due_to_max_qty(ticker, info):
                    continue

                queue.append((ticker, qty, currency))

        # Sort queue (sells before buys)
        queue.sort(key=lambda x: x[1])
        return queue

    def _calculate_leverage_qty(self, ticker: str, info: dict, balance) -> int:
        """Calculate quantity based on leverage swing strategy."""
        # Get current profit rate for the ticker
        profit_rate = self._get_profit_rate(ticker, balance)

        base_qty = info.get('qty', 1)
        profit_target = info.get('profit_target', 0.1)

        # Sell if profit target is reached
        if profit_rate >= profit_target:
            current_qty = self.get_stock(ticker)
            return -int(current_qty) if current_qty > 0 else 0

        # Buy logic: double quantity during negative profit
        if profit_rate >= 0:
            return base_qty
        else:
            return 2 * base_qty

    def _get_profit_rate(self, ticker: str, balance) -> float:
        """Get profit rate for specific ticker."""
        stock = balance.get_stock_by_symbol(ticker)
        return stock.profit if stock else 0.0

    def _should_skip_due_to_max_qty(self, ticker: str, info: dict) -> bool:
        """Check if ticker should be skipped due to max quantity constraint."""
        if 'max_qty' in info:
            if self.acnt.check_max_qty(ticker, info['max_qty']):
                return True
        return False

    def _execute_order_queue(self, queue: List[Tuple[str, int, str]]) -> None:
        """Execute all orders in the queue."""
        self.send_msg(f"Executing {len(queue)} leverage swing orders")

        for ticker, qty, currency in queue:
            try:
                self.order(ticker=ticker, qty=qty, currency=currency)
            except Exception as e:
                self.send_msg(f"Order failed for {ticker}: {str(e)}")
                continue
