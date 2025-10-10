import math
import time
from typing import Optional

import pykis

from .base import BaseAccount
from .models import Balance, Stock


class KisAccount(BaseAccount):
    """KIS (Korea Investment & Securities) Account implementation."""

    name: str = "KisAccount"

    def __init__(self, id: str, appkey: str, secretkey: str, acc_no: str):
        """Initialize KIS account."""
        super().__init__(acc_no=acc_no)
        self.kis = pykis.PyKis(
            id=id,
            appkey=appkey,
            secretkey=secretkey,
            account=acc_no,
            keep_token=True,  # API 접속 토큰 자동 저장
        )

    def _adjust_price_to_tick_size(self, price: float, currency: str = "KRW") -> float:
        """Adjust price to proper tick size based on currency/market."""
        if currency == "USD":
            # US stocks: $0.01 (1 cent) unit for stocks >= $1
            # $0.0001 (0.1 mil) unit for stocks < $1
            if price >= 1.0:
                return round(price, 2)  # Round to 1 cent
            else:
                return round(price, 4)  # Round to 0.1 mil
        else:
            # Korean stocks: Complex tick size rules
            if price < 1000:
                # Under 1,000 won: 1 won unit
                return round(price)
            elif price < 5000:
                # 1,000 ~ 4,999 won: 5 won unit
                return round(price / 5) * 5
            elif price < 10000:
                # 5,000 ~ 9,999 won: 10 won unit
                return round(price / 10) * 10
            elif price < 50000:
                # 10,000 ~ 49,999 won: 50 won unit
                return round(price / 50) * 50
            elif price < 100000:
                # 50,000 ~ 99,999 won: 100 won unit
                return round(price / 100) * 100
            elif price < 500000:
                # 100,000 ~ 499,999 won: 500 won unit
                return round(price / 500) * 500
            else:
                # 500,000 won and above: 1,000 won unit
                return round(price / 1000) * 1000

    def get_balance(self) -> Balance:
        """Return account balance with typed data structure."""
        try:
            balance_raw = self.kis.account().balance()

            # Convert to our data model
            stocks = []
            for stock_data in balance_raw.stocks:
                stock = Stock(
                    symbol=stock_data.symbol,
                    amount=float(stock_data.amount),
                    market=stock_data.market,
                    profit=getattr(stock_data, 'profit', 0.0),
                )
                stocks.append(stock)

            balance = Balance(
                deposits=balance_raw.deposits,
                stocks=stocks,
                account_number=getattr(balance_raw, 'account_number', None),
            )
            return balance
        except Exception as e:
            self.messenger.send_msg(f"Error getting balance: {str(e)}")
            raise

    def get_cash(self, currency: str) -> float:
        """Get available cash for specified currency."""
        try:
            ticker = "379800" if currency == "KRW" else "QQQ"
            stock = self.kis.stock(ticker)
            return float(stock.orderable_amount(price=1).amount)
        except Exception as e:
            self.messenger.send_msg(f"Error getting cash for {currency}: {str(e)}")
            return 0.0

    def get_stock_price(
        self,
        ticker: str,
        action: str = "buy",
        currency: str = "KRW",
    ) -> float:
        """Get current stock price for specified action."""
        try:
            stock = self.kis.stock(ticker)

            try:
                order_book = stock.orderbook()
                price = (
                    order_book.ask_price.price
                    if action == "buy"
                    else order_book.bid_price.price
                )
            except:
                price = stock.quote().high if action == "buy" else stock.quote().low

            # Adjust price to proper tick size based on currency
            price = self._adjust_price_to_tick_size(float(price), currency)
            return price
        except Exception as e:
            self.messenger.send_msg(f"Error getting price for {ticker}: {str(e)}")
            return 0.0

    def get_qty_stock(self, ticker: str) -> float:
        """Get current quantity of specified stock."""
        try:
            balance = self.kis.account().balance()
            qty = 0.0
            for stock_data in balance.stocks:
                if ticker == stock_data.symbol:
                    qty = float(stock_data.qty)
                    break

            self.messenger.send_msg(f"{ticker} in {balance.account_number}: {qty}")
            return qty
        except Exception as e:
            self.messenger.send_msg(f"Error getting quantity for {ticker}: {str(e)}")
            return 0.0

    def order(
        self,
        ticker: str,
        amount: Optional[float] = None,
        qty: Optional[float] = None,
        currency: Optional[str] = None,
    ) -> None:
        """Place order for specified stock."""
        try:
            # Calculate quantity if not provided
            if qty is None and amount is not None:
                current_price = self.get_stock_price(ticker, currency=currency or "KRW")
                qty = amount / current_price
            elif qty is None:
                raise ValueError("Either amount or qty must be provided")

            qty = math.floor(abs(qty)) * (1 if qty > 0 else -1)

            # Skip if quantity is 0
            if qty == 0:
                self.messenger.send_msg(f"Order quantity is 0 for {ticker}, skipping")
                return

            action = "buy" if qty > 0 else "sell"

            # Get fresh price and validate cash availability
            trade_price = self.get_stock_price(ticker, action, currency or "KRW")

            if action == "buy":
                cash = self.get_cash(currency or "KRW")
                while qty * trade_price > cash and qty > 0:
                    qty -= 1

                if qty <= 0:
                    self.messenger.send_msg(f"Insufficient cash for {ticker} order")
                    return

            # Execute order
            stock = self.kis.stock(ticker)
            order_method = getattr(stock, action)
            order = order_method(qty=abs(qty), price=trade_price)

            # Wait for order completion with price adjustment
            rate = 1.001 if action == "buy" else 0.999
            cnt = 0

            while order.pending:
                time.sleep(1)
                cnt += 1

                # Adjust price periodically
                if cnt % 100 == 0:
                    trade_price *= rate
                    # Adjust to proper tick size
                    trade_price = self._adjust_price_to_tick_size(
                        trade_price,
                        currency or "KRW",
                    )
                    order = order_method(qty=abs(qty), price=trade_price)

                # Break after timeout
                if cnt % 1000 == 0:
                    self.messenger.send_msg(f"Order timeout for {ticker}, breaking")
                    break

            # Log the successful order
            super().order(ticker=ticker, qty=qty, currency=currency)

        except Exception as e:
            error_msg = getattr(e, 'msg1', str(e))
            self.messenger.send_msg(f"Order failed for {ticker}: {error_msg}")
            raise
