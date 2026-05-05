from abc import abstractmethod
from datetime import datetime
from typing import Optional

from pytz import timezone

from auto_trader.constants import DEFAULT_AMOUNT_LIMIT
from auto_trader.utils import Messenger

from .models import Balance


class BaseAccount:
    """Base account class"""

    name: str = "BaseAccount"
    amt_limit: int = DEFAULT_AMOUNT_LIMIT

    def __init__(self, acc_no: str, **kwargs):
        """initialize."""
        self.acc_no = acc_no
        self.messenger = Messenger(acc_no)

    @abstractmethod
    def get_balance(self) -> Balance:
        """Get account balance with deposits and stocks."""
        pass

    @abstractmethod
    def get_cash(self, currency: str) -> float:
        """Get cash of account for specified currency."""
        pass

    @abstractmethod
    def get_stock_price(self, ticker: str, action: str = "buy") -> float:
        """Get current price of stock for specified action (buy/sell)."""
        pass

    @abstractmethod
    def get_qty_stock(self, ticker: str) -> float:
        """Get quantity of stock which has name ticker."""
        pass

    def order(
        self,
        ticker: str,
        amount: Optional[float] = None,
        qty: Optional[float] = None,
        currency: Optional[str] = None,
    ) -> None:
        """Order stock by amount or quantity.

        Args:
            ticker: Stock symbol to trade
            amount: Amount in currency to trade (positive=buy, negative=sell)
            qty: Quantity to trade (positive=buy, negative=sell)
            currency: Currency for the trade
        """
        if amount is None and qty is None:
            raise ValueError("Either amount or qty must be provided")

        if qty is None:
            current_price = self.get_stock_price(ticker)
            qty = amount / current_price

        action = "buy" if qty > 0 else "sell"
        current_price = self.get_stock_price(ticker, action)

        # Log the order (base implementation just logs)
        self.messenger.send_msg(
            f'{action} {abs(qty):.4f} of {ticker} at {current_price:.2f}',
        )

        # Log current holdings after order
        current_qty = self.get_qty_stock(ticker)
        self.messenger.send_msg(f"Current holdings of {ticker}: {current_qty}")

    def check_max_qty(self, ticker: str, max_qty: float) -> bool:
        """Check if current holdings exceed max quantity."""
        qty = self.get_qty_stock(ticker)
        if qty > max_qty:
            self.messenger.send_msg(
                f"Already have {qty} > max qty {max_qty} of {ticker}",
            )
            return True
        return False
