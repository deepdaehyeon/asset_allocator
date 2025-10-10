from collections import defaultdict
from typing import Dict, List, Set

from auto_trader.constants import DEFAULT_THRESHOLD, MARKET_MAPPING, MIN_ORDER_AMOUNT
from auto_trader.utils import handle_exceptions

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

    @handle_exceptions(reraise=True)
    def run(self) -> None:
        """Allocate assets based on configuration."""
        balance = self.get_balance()

        for currency in balance.deposits.keys():
            if currency not in self.config.keys():
                continue

            self._allocate_currency(currency, balance)

    def _allocate_currency(self, currency: str, balance) -> None:
        """Allocate assets for specific currency."""
        # Extract configuration
        currency_config = self._extract_currency_config(currency)
        threshold = currency_config['threshold']
        assets_config = currency_config['assets']

        # Calculate current amounts
        amt = self._calculate_current_amounts(currency, balance)
        amt_total = sum(amt.values())

        if amt_total == 0:
            self.send_msg(f"No assets found for {currency}")
            return

        # Validate target ratios
        if not self._validate_target_ratios(assets_config, currency):
            return

        # Check if rebalancing is needed
        if not self._should_rebalance(
            amt,
            amt_total,
            assets_config,
            threshold,
            currency,
        ):
            return

        # Execute rebalancing
        self._execute_rebalancing(assets_config, amt, amt_total, currency, balance)

    def _extract_currency_config(self, currency: str) -> Dict:
        """Extract and normalize currency configuration."""
        currency_config = self.config[currency]

        # Extract threshold and assets from config
        if isinstance(currency_config, dict) and 'assets' in currency_config:
            # New nested structure
            threshold = currency_config.get('threshold', self.threshold)
            assets_config = currency_config['assets']
        else:
            # Legacy flat structure
            threshold = self.threshold
            assets_config = currency_config

        return {'threshold': threshold, 'assets': assets_config}

    def _calculate_current_amounts(self, currency: str, balance) -> Dict[str, float]:
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

    def _validate_target_ratios(
        self,
        assets_config: Dict[str, float],
        currency: str,
    ) -> bool:
        """Validate that target ratios don't exceed 100%."""
        total_ratio = sum(assets_config.values())
        if total_ratio > 1.0:
            self.send_msg(
                f"ERROR: Sum of ratios ({total_ratio:.3f}) is larger than 1.0 for {currency}",
            )
            return False
        return True

    def _should_rebalance(
        self,
        amt: Dict[str, float],
        amt_total: float,
        assets_config: Dict[str, float],
        threshold: float,
        currency: str,
    ) -> bool:
        """Check if rebalancing is needed based on threshold."""
        # Calculate current ratios
        current_allocations = self._calculate_current_ratios(
            amt,
            amt_total,
            assets_config,
        )

        # Calculate ratio difference
        ratio_diff = self._calculate_ratio_difference(
            assets_config,
            current_allocations,
        )

        if ratio_diff < threshold:
            self.send_msg(
                f"Ratio difference is {ratio_diff*100:.1f}% less than {threshold*100:.1f}% for {currency}, "
                "so don't activate rebalancing",
            )
            return False

        return True

    def _calculate_current_ratios(
        self,
        amt: Dict[str, float],
        amt_total: float,
        assets_config: Dict[str, float],
    ) -> Dict[str, float]:
        """Calculate current asset ratios."""
        current_ratios: Dict[str, float] = defaultdict(float)

        # Get all relevant stocks
        relevant_assets = set(amt.keys()).union(set(assets_config.keys()))

        # Calculate ratios
        for asset_name in relevant_assets:
            current_ratios[asset_name] = amt[asset_name] / amt_total

        return current_ratios

    def _calculate_ratio_difference(
        self,
        target_ratio: Dict[str, float],
        current_ratio: Dict[str, float],
    ) -> float:
        """Calculate total ratio difference between target and current."""
        all_assets = set(target_ratio.keys()).union(set(current_ratio.keys()))
        ratio_diff = 0.0

        for asset in all_assets:
            diff = abs(target_ratio.get(asset, 0.0) - current_ratio.get(asset, 0.0))
            ratio_diff += diff

        return ratio_diff

    def _execute_rebalancing(
        self,
        ratio: Dict[str, float],
        amt: Dict[str, float],
        amt_total: float,
        currency: str,
        balance,
    ) -> None:
        """Execute rebalancing orders."""
        # Get all relevant stocks
        stock_list = self._get_relevant_stocks(currency, balance, ratio)

        # Calculate and sort orders
        order_queue = self._calculate_order_queue(
            stock_list,
            ratio,
            amt,
            amt_total,
            currency,
        )

        self.send_msg(f"Executing {len(order_queue)} rebalancing orders for {currency}")

        # Execute orders
        self._execute_order_queue(order_queue)

    def _get_relevant_stocks(
        self,
        currency: str,
        balance,
        ratio: Dict[str, float],
    ) -> List[str]:
        """Get list of all relevant stocks for rebalancing."""
        stock_list: List[str] = []

        # Add currently held stocks
        currency_markets = MARKET_MAPPING.get(currency, [])
        for stock in balance.stocks:
            if stock.market in currency_markets:
                stock_list.append(stock.symbol)

        # Add configured stocks that might not be currently held
        for ticker in ratio.keys():
            if ticker not in stock_list:
                stock_list.append(ticker)

        return stock_list

    def _calculate_order_queue(
        self,
        stock_list: List[str],
        ratio: Dict[str, float],
        amt: Dict[str, float],
        amt_total: float,
        currency: str,
    ) -> List[tuple]:
        """Calculate order queue with amounts and priorities."""
        order_queue: List[tuple] = []

        for ticker in stock_list:
            amt_target = ratio.get(ticker, 0.0) * amt_total
            amt_diff = amt_target - amt.get(ticker, 0.0)

            if (
                abs(amt_diff) > MIN_ORDER_AMOUNT
            ):  # Only order if difference is significant
                order_queue.append((ticker, amt_diff, currency))

        # Sort queue (sell orders first, then buy orders)
        order_queue.sort(key=lambda x: x[1])
        return order_queue

    def _execute_order_queue(self, order_queue: List[tuple]) -> None:
        """Execute all orders in the queue."""
        for ticker, amt_diff, currency in order_queue:
            try:
                self.order(ticker=ticker, amount=amt_diff, currency=currency)
            except Exception as e:
                self.send_msg(f"Order failed for {ticker}: {str(e)}")
                continue
