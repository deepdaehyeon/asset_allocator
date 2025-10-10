import hashlib
import time
import uuid
from typing import Optional
from urllib.parse import unquote, urlencode
import os

import jwt
import requests

from auto_trader.constants import MIN_CRYPTO_QUANTITY, UPBIT_API_BASE_URL
from auto_trader.utils import handle_exceptions

from .base import BaseAccount
from .models import Balance, Stock


class UpbitAccount(BaseAccount):
    """Upbit cryptocurrency exchange account implementation."""

    name: str = "UpbitAccount"

    def __init__(self, **kwargs):
        super().__init__(acc_no="upbit")
        self.access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
        self.secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']

    @handle_exceptions(reraise=True)
    def get_balance(self) -> Balance:
        """Return account balance with typed data structure."""
        headers = self._compose_header()
        res = requests.get(
            UPBIT_API_BASE_URL + '/v1/accounts',
            params={},
            headers=headers,
        ).json()

        deposits = {}
        stocks = []

        for batch in res:
            if batch['currency'] == 'KRW':
                deposits['KRW'] = float(batch['balance'])
            else:
                # Get current price for profit calculation
                profit = self._calculate_stock_profit(batch)

                stock = Stock(
                    symbol=batch['currency'],
                    amount=float(batch['balance']),
                    market='CRYPTO',
                    profit=profit,
                )
                stocks.append(stock)

        return Balance(deposits=deposits, stocks=stocks)

    def _calculate_stock_profit(self, batch: dict) -> float:
        """Calculate profit for a cryptocurrency holding."""
        try:
            curr_price = self.get_stock_price(ticker=batch['currency'])
            avg_buy_price = float(batch['avg_buy_price'])
            return (
                (curr_price - avg_buy_price) / avg_buy_price
                if avg_buy_price > 0
                else 0.0
            )
        except:
            return 0.0

    @handle_exceptions(default_return=0.0, reraise=False)
    def get_cash(self, currency: str = "KRW") -> float:
        """Get available cash (KRW balance)."""
        headers = self._compose_header()
        res = requests.get(
            UPBIT_API_BASE_URL + '/v1/accounts',
            params={},
            headers=headers,
        ).json()

        for batch in res:
            if batch['currency'] == 'KRW':
                return float(batch['balance'])

        self.messenger.send_msg("No KRW balance found in account")
        return 0.0

    @handle_exceptions(default_return=0.0, reraise=False)
    def get_stock_price(self, ticker: str, action: str = "buy") -> float:
        """Get current price of cryptocurrency."""
        params = {"markets": f"KRW-{ticker}"}
        res = requests.get(UPBIT_API_BASE_URL + "/v1/ticker", params=params).json()
        return float(res[0]['trade_price'])

    @handle_exceptions(default_return=0.0, reraise=False)
    def get_qty_stock(self, ticker: str) -> float:
        """Get current quantity of specified cryptocurrency."""
        headers = self._compose_header()
        res = requests.get(
            UPBIT_API_BASE_URL + '/v1/accounts',
            params={},
            headers=headers,
        ).json()

        for batch in res:
            if batch['currency'] == ticker:
                qty = float(batch['balance'])
                self.messenger.send_msg(f"{ticker} in upbit account: {qty}")
                return qty

        self.messenger.send_msg(f"{ticker} not found in upbit account: 0")
        return 0.0

    @handle_exceptions(reraise=True)
    def order(
        self,
        ticker: str,
        amount: Optional[float] = None,
        qty: Optional[float] = None,
        currency: Optional[str] = None,
    ) -> None:
        """Place order for specified cryptocurrency."""
        # Calculate and validate quantity
        qty = self._calculate_crypto_quantity(ticker, amount, qty)
        if qty == 0:
            self.messenger.send_msg(f"Order quantity is 0 for {ticker}, skipping")
            return

        action = 'bid' if qty > 0 else "ask"

        # Validate cash for buy orders
        if action == 'bid' and not self._validate_crypto_cash(ticker, qty):
            return

        # Execute the order
        self._execute_upbit_order(ticker, qty, action)

        # Log the successful order
        super().order(
            ticker=ticker,
            qty=qty if action == 'bid' else -qty,
            currency="KRW",
        )

    def _calculate_crypto_quantity(
        self,
        ticker: str,
        amount: Optional[float],
        qty: Optional[float],
    ) -> float:
        """Calculate cryptocurrency order quantity."""
        if qty is None and amount is not None:
            current_price = self.get_stock_price(ticker)
            qty = amount / current_price
        elif qty is None:
            raise ValueError("Either amount or qty must be provided")

        # Round to 6 decimal places for crypto
        qty = round(abs(qty), 6)
        return qty

    def _validate_crypto_cash(self, ticker: str, qty: float) -> bool:
        """Validate sufficient cash for crypto purchase."""
        trade_price = self.get_stock_price(ticker, "bid")
        cash = self.get_cash()
        required_cash = qty * trade_price

        if required_cash > cash:
            self.messenger.send_msg(
                f"Insufficient cash for {ticker}: need {required_cash}, have {cash}",
            )
            return False
        return True

    def _execute_upbit_order(self, ticker: str, qty: float, action: str) -> None:
        """Execute order through Upbit API."""
        trade_price = self.get_stock_price(ticker, action)

        # Prepare order parameters
        params = dict(
            market=f'KRW-{ticker}',
            side=action,
            ord_type="limit",
            volume=str(qty),
            price=str(trade_price),
        )

        # Execute order
        headers = self._compose_header(params)
        res = requests.post(
            UPBIT_API_BASE_URL + '/v1/orders',
            json=params,
            headers=headers,
        )

        if res.status_code == 200:
            order_result = res.json()
            self.messenger.send_msg(
                f"Order placed: {order_result.get('uuid', 'unknown')}",
            )
        else:
            error_msg = res.json().get('error', {}).get('message', 'Unknown error')
            self.messenger.send_msg(f"Order failed: {error_msg}")
            raise Exception(f"Order failed: {error_msg}")

    @handle_exceptions(reraise=True)
    def _compose_header(self, params: Optional[dict] = None) -> dict:
        """Compose authentication header for Upbit API."""
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': round(time.time() * 1000),
        }

        if params is not None:
            query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            payload.update(
                {
                    'query_hash': query_hash,
                    'query_hash_alg': 'SHA512',
                },
            )

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }
        return headers
