from __future__ import annotations
from typing import *
import json

import requests

from coinbase.auth import CoinbaseAuth


class Public(object):
    def __init__(self, sandbox: bool = False):
        self.sandbox = sandbox
        if sandbox:
            self.url = "https://api-public.sandbox.pro.coinbase.com"
        else:
            self.url = "https://api.pro.coinbase.com"
        
        self.headers = {"Accept": "application/json"}
            
    def __repr__(self):
        return f"CoinbasePro_PublicAPI_Wrapper(url={self.url}, sandbox={self.sandbox})"
        
    def request(self, endpoint: str, params: dict = None):
        """
        -------
        Public API only allows GET requests.
        -------
        PARAMS
        -------
            1. 'endpoint' -> REST API endpoint to concatenate to self.url
            2. 'params' -> HTTP request parameters
        -------
        """
        r = requests.get(url=self.url+endpoint, headers=self.headers, params=params)
        return r.json()
    
    def get_product(self, product_id: str):
        """
        ----------
        Returns
        ----------
            {'id': 'BTC-USD',
             'base_currency': 'BTC',
             'quote_currency': 'USD',
             'base_min_size': '0.000016',
             'base_max_size': '1500',
             'quote_increment': '0.01',
             'base_increment': '0.00000001',
             'display_name': 'BTC/USD',
             'min_market_funds': '1',
             'max_market_funds': '20000000',
             'margin_enabled': True,
             'fx_stablecoin': False,
             'max_slippage_percentage': '0.10000000',
             'post_only': False,
             'limit_only': False,
             'cancel_only': False,
             'trading_disabled': False,
             'status': 'online',
             'status_message': '',
             'auction_mode': False}
        """
        return self.request(endpoint=f"/products/{product_id}")
        
    def get_all_products(self):
        """
        ----------
        Returns
        ----------
             A list of products, where each is represented like the output of get_product method
        ----------
        """
        return self.request(endpoint="/products")
    
    def get_last_tick(self, product_id: str):
        """
        ----------
        Returns
        ----------
            {"trade_id": 86326522,
              "price": "6268.48",
              "size": "0.00698254",
              "time": "2020-03-20T00:22:57.833897Z",
              "bid": "6265.15",
              "ask": "6267.71",
              "volume": "53602.03940154"}
        ----------
        """
        return self.request(endpoint=f"/products/{product_id}/ticker")
    
    def get_product_stats(self, product_id: str):
        """
        ----------
        Returns 
        ----------
        24 hour stats (OHLC), last tick, as well as 30-day volume
            {'open': '42789.66',
             'high': '42907.12',
             'low': '41766.79',
             'last': '42283.11',
             'volume': '11970.31835578',
             'volume_30day': '503832.06464632'}
        ----------
        """
        return self.request(endpoint=f"/products/{product_id}/stats")
    
    def get_product_book(self, product_id: str, level: int = 1):
        """
        ----------
        PARAMS
        ----------
            1. 'product_id' -> currency pair; example "BTC-USD"
            2. 'level' -> depth of results
                        > (level=1) The best bid, ask and auction info
                        > (level=2) Full order book (aggregated) and auction info
                        > (level=3) Full order book (non aggregated) and auction info
                        > For levels 1 and 2:
                                [[price, size, num_orders]]
                            - 'price' -> price of the bid/ask
                            - 'size' -> sum of the size of the orders at that price
                            - 'num-orders' -> count of orders at that price
        ----------
        Returns 
        ----------
            {'bids': [[price, size, num_orders]],
             'asks': [[price, size, num_orders]],
             'sequence': 35441062744,
             'auction_mode': False,
             'auction': None}
            
            1. For bids and asks:
                    > 
         ----------
        """
        assert 1 <= level <= 3, "'level' must be in range (1,3)"
        return self.request(endpoint=f"/products/{product_id}/book?level={level}")
    
    def get_candles(self, 
                    product_id: str, 
                    start: str = None, 
                    end: str = None, timeframe: int = None):
        """
        ----------
        Params
        ----------
            1. product_id -> currency pai2
            2. start -> start time in ISO 8601
            3. end -> end time in ISO 8601
            4. timeframe -> timeframe in seconds
                          > allowed values: {60, 300, 900, 3600, 21600, 86400}
                          > [1min, 5min, 15min, 1hr, 6hr, 1d]
        ----------
        Returns
        ----------
            [timestamp, price_low, price_high, price_open, price_close, volume]
        """
        params = {}
        if start is not None:
            params.update({"start": start})
        if end is not None:
            params.update({"end": end})
        if timeframe is not None:
            assert timeframe in [60, 300, 900, 3600, 21600, 86400], "timeframe must be denoted in seconds. Allowed values: {60, 300, 900, 3600, 21600, 86400}"
            params["granularity"] = str(timeframe)
        if len(params) == 0:
            params = None
        return self.request(endpoint=f"/products/{product_id}/candles", params=params)

    def get_time(self):
        """
        ---------
        Get the API server time
        ---------
        Returns
        ---------
            {'iso': '2022-03-23T15:15:24.985Z', 'epoch': 1648048524.985}
        ---------
        """
        return self.request(endpoint="/time")


class Private(object):
    """
    ---------------
    CoinbasePro API Wrapper
    ---------------
    API Documentation
    ---------------
        https://docs.cloud.coinbase.com/exchange/reference/
        https://docs.cloud.coinbase.com/exchange/docs/
    ---------------
    PARAMS
    ---------------
        1. 'b64_secret_key' -> Base-64 encoded secret key, provided (already in base64) by Coinbase when you generate api keys
        2. 'api_key' -> API key provided by Coinbase
        3. 'passphrase' -> Passphrase you created when generating api keys on Coinbase
        4. 'sandbox' -> Whether or not to point to the sandbox environment or not; Default True
                        Use the sandbox environment for development purposes. 
    ---------------
    """
    def __init__(self, b64_secret_key: str, api_key: str, passphrase: str, sandbox: bool = True):
        self.sk = b64_secret_key
        self.api_key = api_key
        self.passphrase = passphrase
        self.sandbox = sandbox
        if sandbox:
            self.url = "https://api-public.sandbox.pro.coinbase.com"
        else:
            self.url = "https://api.pro.coinbase.com"
    
    def __repr__(self):
        return f"CoinbasePro_API_Wrapper(url={self.url}, sandbox={self.sandbox})"
    
    @classmethod
    def from_file(cls, filepath: str, sandbox: bool = True) -> Private:
        assert filepath[-5:] == ".json", "'filepath' must point to a json file"
        with open(filepath, "r") as f:
            text = f.read()
        return cls(sandbox=sandbox, **json.loads(text))
        
    def request(self, method: str, endpoint: str, data: str = None, params=None):
        """
        -------
        PARAMS
        -------
            1. 'method' -> HTTP method; GET POST or DELETE
            2. 'endpoint' -> REST API endpoint to concatenate to self.url
            3. 'data' -> data (json-encoded string payload) to post for POST requests
            4. 'params' -> HTTP request parameters
        -------
        """
        method = method.upper()
        assert method in ["GET", "POST", "DELETE"]
        auth = CoinbaseAuth(sk=self.sk, api_key=self.api_key, passphrase=self.passphrase)
        if method == "GET":
            r = requests.get(url=self.url+endpoint, params=params, auth=auth)
        elif method == "POST":
            assert data is not None, "Need to specify data to post for POST requests."
            r = requests.post(url=self.url+endpoint, data=data, params=params, auth=auth)
        elif method == "DELETE":
            r = requests.delete(url=self.url+endpoint, params=params, auth=auth)
        return r.json()
    
    def get_account(self, account_id: str, **kwargs) -> Dict:
        """
        ----------
        Returns
        ----------
            A Dictionary representing an account
                {'id': '',
                  'currency': '',
                  'balance': '',
                  'hold': '',
                  'available': '',
                  'profile_id': '',
                  'trading_enabled': True}
        ----------
        """
        endpoint = "/accounts/" + account_id
        data = self.request(method="GET", endpoint=endpoint)
        currency_filter = kwargs["currency_filter"]
        balance_filter = kwargs["has_balance_filter"]
        
        if not currency_filter is None:
            assert isinstance(currency_filter, list), "currency_filter must be a list of currencies to keep."
            data = [d for d in data if d["currency"] in currency_filter]
        elif not balance_filter is None:
            assert isinstance(balance_filter, bool), "has_balance_filter must be True, False, or None"
            if balance_filter:
                data = [d for d in data if float(d["balance"]) > 0]
            else:
                data = [d for d in data if float(d["balance"]) == 0]
        return data
        
    def get_all_accounts(self, currency_filter: List[str] = None, has_balance_filter: bool = None) -> List[Dict]:
        """
        ----------
        Returns
        ----------
            List of dictionaries where each dictionary is the same represention as get_account method
        ----------
        PARAMS
        ----------
            1. 'currency_filter' -> a list of currencies to filter by 
                                    example: ["BTC", "ETH"]
            2. 'has_balance_filter' -> filter by accounts that has or doesn't have balances
                                    True -> keeps accounts with balances
                                    False -> keeps accounts without balances
        ----------
        """
        return self.get_account(account_id="", currency_filter=currency_filter, has_balance_filter=has_balance_filter)
    
    def get_all_wallets(self, currency_filter: List[str] = None, type_filter: str = None):
        endpoint = "/coinbase-accounts/"
        data = self.request(method="GET", endpoint=endpoint)
        if not currency_filter is None:
            assert isinstance(currency_filter, list), "'currency_filter' must be a list of currencies to keep."
            data = [d for d in data if d["currency"] in currency_filter]
        if not type_filter is None:
            assert type_filter in ["fiat", "wallet"], "'type_filter' must be either fiat, wallet, or None"
            data = [d for d in data if d["type"] == type_filter]
        return data
    
    def get_order(self, order_id: str) -> dict:
        endpoint = f"/orders/{order_id}"
        return self.request(method="GET", endpoint=endpoint)
    
    def get_all_orders(self, 
                       product_id: str = None, 
                       limit: int = 100, 
                       status: Union[list, str] = ["open", "pending", "active"]) -> List[dict]:
        """
        ---------
        PARAMS
        ---------
            1. product_id -> Optional. filters orders by a product_id (ex; "BTC-USD")

            2. limit ->  Required. Num of results to show.

            3. status -> Required. Limit list of orders to this status or statuses. 
                    > Passing 'all' returns orders of all statuses.
                    > List Element Options: [open, pending, active, done, settled]
                    > default: [open, pending, active]
        ---------
        """
        endpoint = f"/orders/"
        params = {"limit": limit}
        if status == "all":
            params.update({"status": "all"})
        else:  
            allowed_status_options = ["open", "pending", "active", "done", "settled"]
            assert isinstance(status, list), "If not status='all', must pass a list"
            for s in status:
                assert s in allowed_status_options, f"Allowed status options are {allowed_status_options}. You passed {s}"
            params.update({"status": status})
        
        if product_id is not None:
            params.update({"product_id": product_id})
        
        return self.request(method="GET", endpoint=endpoint, params=params)
        
    
    def cancel_order(self, order_id: str):
        """
        Cancels an order by its order_id
        Returns the order_id back to you if successful.
        """
        endpoint = f"/orders/{order_id}"
        return self.request(method="DELETE", endpoint=endpoint)
    
    def cancel_all_orders(self, product_id: str = None):  
        """
        Cancels all open orders
            Optionally choose a product_id to only cancel orders on that product_id
        """
        endpoint = f"/orders"
        params = {"product_id": product_id} if product_id is not None else None     
        return self.request(method="DELETE", endpoint=endpoint, params=params)
    
    def create_order(self, 
                     product_id: str,
                     side: str,
                     order_type: str,
                     **kwargs):
        """
        ------------
        Create an Buy/Sell Order
        ------------
        Reference
            https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_postorders
        ------------
        PARAMS
        ------------
        'product_id' -> Currency pair to trade on; Example: BTC-USD
                        The products list is available via the /products endpoint
        
        'order_type' -> Order Type -- Can be any of the following 3:
                        1. market -> Execute immediately (don't go on open book)
                                   > always a taker (taker fees)
                        2. limit -> Requires price and size. Order fills at price or better.
                        3. stop -> Triggers when price hits 'stop_price'
                        
        'side'  -> 'buy' or 'sell'; which side of the trade 
                        
        **'price' -> only for limit and stop orders; 
                   must be specified in quote_increment (less than 0.01 isn't accepted)
                   
        **'size' -> units of the base currency (BTC in BTCUSD) to buy/sell
                  must be greater than the product base_min_size
                  must be less than base_max_size
                  --> Required for limit/stop orders and market sell orders
        
        **'stop_price' -> Price threshold at which a stop order will be placed on the book
        
        **'stop' -> Either 'loss' or 'entry':
                > 'loss' -> Triggers when the last trade price changes to a value at or below 'price'.
                > 'entry' -> Triggers when the last trade price changes to a value at or above 'price'.
        
        **'time_in_force' -> There are four possible values:
                           1. 'GTC' -> Good til Cxl'd (Default)
                           2. 'GTT' -> Good til Time
                           3. 'IOC' -> Immediate or Cxl
                           4. 'FOK' -> Fill or Kill
        
        **'cancel_after' -> Used for GTT orders; how long to keep the order open until canceling
                        > must be 'min', 'hour', or 'day' (24 hours)
        
        **'post_only' -> If True, the order will only make liquidity (maker only)
                       Invalid when time_in_force is IOC or FOK
                  
        **'funds' -> Optional and used for market orders. You can specify to buy BTC for this amount of
                   the quote currency (USD in BTCUSD)
        
        ---------------
        Market Order Required Parameters
        ---------------
            size	[optional]* Desired amount in BTC
            funds	[optional]* Desired amount of quote currency to use
            * One of size or funds is required.
        ---------------
        Limit Order Required Parameters
        ---------------
            price	Price per bitcoin
            size	Amount of BTC to buy or sell
            time_in_force	[optional] GTC, GTT, IOC, or FOK (default is GTC)
            cancel_after	[optional]* min, hour, day
            post_only	[optional]** Post only flag
            * Requires time_in_force to be GTT
            ** Invalid when time_in_force is IOC or FOK
        ---------------
        """

        if "time_in_force" in kwargs:
            if kwargs.get("time_in_force") == "GTT":
                assert "cancel_after" in kwargs, "Param 'cancel_after' is needed for GTT (Good til Time) trades."
            elif kwargs.get("time_in_force") in ["IOC", "FOK"]: #post_only is invalid if IOC or FOK
                assert not "post_only" in kwargs, "If placing IOC or FOK trades, post_only is invalid."
        
        if order_type == "market":
            #boolean XOR by using bitwise XOR operator
            assert ("funds" in kwargs) ^ ("size" in kwargs), "For market orders, either 'funds' or 'size' must be specified, but not both."
        
        elif order_type == "limit":
            assert "size" in kwargs and "price" in kwargs, "For limit orders, 'size' and 'price' must be specified."
        
        elif order_type == "stop":
            assert "stop" in kwargs and "stop_price" in kwargs, "For stop orders, specify both 'stop' and 'stop_price'"
            assert "size" in kwargs and "price" in kwargs, "For stop orders, specify 'size' and 'price'"
            
        payload = self.create_payload(order_type=order_type, product_id=product_id, side=side, **kwargs)
        
        return self.request(method="POST", endpoint="/orders", data=payload)
    
    def create_payload(self, order_type: str, product_id: str, side: str, **kwargs) -> str:
        """
        Creates the payload to create trades
        Returns a json string
        """
        payload = {
            "type": order_type,
            "side": side,
            "product_id": product_id,
            "stp": "dc",
            "time_in_force": "GTC"
        }
        if order_type == "stop": #type should be emtpy if a stop order
            del payload["type"]
        payload.update(kwargs)
        payload = dict([(k, str(v)) for k,v in payload.items()])
        return json.dumps(payload)
    
    def limit_buy(self, product_id: str, price: float, size: float, **kwargs):
        return self.create_order(order_type="limit", 
                                 side="buy",
                                 product_id=product_id, 
                                 price=price, 
                                 size=size, 
                                 **kwargs)
    
    def limit_sell(self, product_id: str, price: float, size: float, **kwargs):
        return self.create_order(order_type="limit", 
                                 side="sell", 
                                 product_id=product_id, 
                                 price=price, 
                                 size=size, 
                                 **kwargs)
    
    def market_buy(self, product_id: str, size: float, **kwargs):
        return self.create_order(order_type="market", 
                                 side="buy", 
                                 product_id=product_id, 
                                 size=size, 
                                 **kwargs)
    
    def market_sell(self, product_id: str, size: float, **kwargs):
        return self.create_order(order_type="market", 
                                 side="sell", 
                                 product_id=product_id, 
                                 size=size, 
                                 **kwargs)
    
    def stop_loss(self, product_id: str, stop_price: float, price: float, size: float, **kwargs):
        return self.create_order(order_type="stop", 
                                 side="sell", 
                                 stop="loss",
                                 product_id=product_id,
                                 stop_price=stop_price, #triggers a limit order at param 'price'
                                 price=price, #price to actually sell
                                 size=size,
                                 **kwargs)

    def stop_entry(self, product_id: str, stop_price: float, price: float, size: float, **kwargs):
        return self.create_order(order_type="stop", 
                                 side="buy", 
                                 stop="entry",
                                 product_id=product_id,
                                 stop_price=stop_price, #triggers a limit order at param 'price'
                                 price=price, #price to actually buy
                                 size=size,
                                 **kwargs)
        
    
    def get_order_status(self, order_id: str) -> str:
        order = self.get_order(order_id)
        return order["status"]
    
    
