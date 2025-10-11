from abc import abstractmethod
from typing import List, Optional

from auto_trader.account.base import BaseAccount
from auto_trader.account.models import Balance
from auto_trader.constants import DEFAULT_AMOUNT_LIMIT, MARKET_MAPPING


class BaseAgent:
    """Base trading agent class."""

    name: str = "BaseAgent"
    amt_limit: int = DEFAULT_AMOUNT_LIMIT

    def __init__(self, acnt: BaseAccount, config: dict, forced: bool =False):
        """Initialize agent with account and configuration."""
        self.acnt = acnt
        self.config = config
        self.forced = forced

    @abstractmethod
    def run(self) -> None:
        """Execute the trading strategy."""
        pass

    def get_balance(self) -> Balance:
        """Get account balance."""
        return self.acnt.get_balance()

    def get_cash(self, currency: str) -> float:
        """Get available cash for specified currency."""
        return self.acnt.get_cash(currency)

    def get_stock(self, symbol: str) -> float:
        """Get current holdings of specified stock."""
        return self.acnt.get_qty_stock(symbol)

    def get_stock_list(self, currency: str) -> List[str]:
        """Get list of stocks for specified currency."""
        balance = self.get_balance()
        markets = MARKET_MAPPING.get(currency, [])
        return [stock.symbol for stock in balance.stocks if stock.market in markets]

    def order(
        self,
        ticker: str,
        amount: Optional[float] = None,
        qty: Optional[float] = None,
        currency: Optional[str] = None,
    ) -> None:
        """Place an order for specified ticker."""
        return self.acnt.order(ticker=ticker, amount=amount, qty=qty, currency=currency)

    def send_msg(self, message: str) -> None:
        """Send message via messenger."""
        return self.acnt.messenger.send_msg(message)
