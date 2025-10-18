import fcntl
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

from auto_trader.constants import DEFAULT_THRESHOLD, MARKET_MAPPING, MIN_ORDER_AMOUNT

from .base import BaseAgent


class AssetAllocateAgent(BaseAgent):
    """Asset allocation agent class.

    [Config example]
    "$acc_no":
        "KRW":
            "threshold": 0.05
            "assets":
                "379800": 0.1
                "379810": 0.1
        "USD":
            "threshold": 0.15
            "assets":
                "MSFT": 0.5
                "GOOGL": 0.5
    """

    name: str = "AssetAllocateAgent"
    threshold: float = DEFAULT_THRESHOLD
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock_file_path = Path("/tmp/asset_allocate_lock")

    def run(self) -> None:
        """Allocate assets based on configuration."""
        # Check if another instance is already running
        if not self._acquire_lock():
            self.send_msg("Another AssetAllocateAgent is already running, skipping execution")
            return
            
        try:
            balance = self.get_balance()

            for currency in balance.deposits.keys():
                if currency not in self.config.keys():
                    continue
                try:
                    # Get configuration
                    currency_config = self.config[currency]
                    threshold = currency_config.get('threshold', self.threshold)
                    target_ratio = currency_config['assets']
                    total_ratio = sum(target_ratio.values())
                    if total_ratio > 1.0:
                        self.send_msg(
                            f"ERROR: Sum of ratios ({total_ratio:.3f}) is larger than 1.0 for {currency}",
                        )

                    # Get current amount
                    amt = self._get_current_amount(currency, balance)
                    amt_total = sum(amt.values())
                    if amt_total == 0:
                        self.send_msg(f"No assets found for {currency}")
                        return

                    # Get current ratio
                    current_ratio: Dict[str, float] = defaultdict(float)
                    all_assets= set(amt.keys()).union(set(target_ratio.keys()))
                    for asset_name in all_assets:
                        current_ratio[asset_name] = amt[asset_name] / amt_total

                    # Check if rebalancing is needed
                    ratio_diff = 0.0
                    for asset in all_assets:
                        diff = abs(target_ratio.get(asset, 0.0) - current_ratio.get(asset, 0.0))
                        ratio_diff += diff
                    if ratio_diff < threshold and not self.forced:
                        self.send_msg(
                            f"Ratio difference is {ratio_diff*100:.1f}% less than {threshold*100:.1f}% for {currency}, "
                            "so don't activate rebalancing",
                        )
                        continue

                    # Execute rebalancing
                    order_queue: List[tuple] = []

                    for ticker in all_assets:
                        amt_target = target_ratio.get(ticker, 0.0) * amt_total
                        amt_diff = amt_target - amt.get(ticker, 0.0)
                        order_queue.append((ticker, amt_diff, currency))

                    # Sort queue (sell orders first, then buy orders)
                    order_queue.sort(key=lambda x: x[1])
                    self.send_msg(f"Executing {len(order_queue)} rebalancing orders for {currency}")

                    # Execute orders
                    self._execute_order_queue(order_queue)
                except Exception as e: 
                    print(e)
        finally:
            self._release_lock()

    def _get_current_amount(self, currency: str, balance) -> Dict[str, float]:
        """Calculate current amounts for all assets in currency."""
        amt: Dict[str, float] = defaultdict(float)

        # Add stock amounts
        currency_markets = MARKET_MAPPING.get(currency, [])
        for stock in balance.stocks:
            if stock.market in currency_markets:
                amt[stock.symbol] = float(stock.amount)

        # Add cash amount
        amt['cash'] = self.get_cash(currency)

        return amt

    def _execute_order_queue(self, order_queue: List[tuple]) -> None:
        """Execute all orders in the queue."""
        for ticker, amt_diff, currency in order_queue:
            self.order(ticker=ticker, amount=amt_diff, currency=currency)

    def _acquire_lock(self) -> bool:
        """Acquire file lock to prevent concurrent execution."""
        try:
            self._lock_file = open(self._lock_file_path, 'w')
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_file.write(f"{os.getpid()}\n")
            self._lock_file.flush()
            return True
        except (IOError, OSError):
            return False

    def _release_lock(self) -> None:
        """Release file lock."""
        try:
            if hasattr(self, '_lock_file'):
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                self._lock_file.close()
                if self._lock_file_path.exists():
                    self._lock_file_path.unlink()
        except (IOError, OSError):
            pass

                
