from __future__ import annotations
import json
import time
from threading import Thread
from typing import *
from websocket import create_connection

from collections import deque

from coinbase.auth import get_timestamp, sign


class WebSocket(object):
    """
    docs: https://docs.cloud.coinbase.com/exchange/docs/websocket-overview
    ---------
    PARAMS
    ---------
    Note it is recommended to create an API key with read only access for this websocket.

        1. 'b64_secret_key' -> base64 encoded secret key provided by coinbase upon api key generation
        2. 'api_key' -> Api key provided by coinbase upon key generation
        3. 'passphrase' -> passphrase you selected upon key generation
        4. 'products' -> a list of products to stream info for; ex: ["BTC-USD", ...]
        5. 'channels' -> list of channels to use. Defined when initailized 
                Allowed Values:
                    a. 'ticker'- real-time price updates every time a match happens;
                            {"type":"ticker",
                             "sequence":29912240,
                             "product_id":"BTC-USD",
                             "price":"40552.26",
                             "open_24h":"40552.26",
                             "volume_24h":"0.43526841",
                             "low_24h":"40552.26",
                             "high_24h":"40662.06",
                             "volume_30d":"160.65999711",
                             "best_bid":"40552.26",
                             "best_ask":"40553.84",
                             "side":"sell",
                             "time":"2022-03-16T18:42:08.145773Z",
                             "trade_id":131414,
                             "last_size":"0.00002465"}
                    b. 'level2' - guarantees delivery of all updates; shows bids/asks
                            {"type": "snapshot",
                             "product_id": "BTC-USD",
                             "bids": [["10101.10", "0.45054140"]],
                             "asks": [["10102.55", "0.57753524"]]}
        6. 'max_memory' -> max items allowed in memory before older items drop off
        7. 'sandbox' -> bool; if True, the sandbox environment is utilized
        8. 'verbose' -> bool; will print updates as new data comes in if True
    -------
    Example Usage
    -------
        >>> websocket = CoinbaseWebSocket.from_file(filepath="prod_creds.json", #read access only
                                                    products=["BTC-USD"], 
                                                    channels=["ticker"],
                                                    sandbox=False)

        >>> websocket.start(interval=30)
        Subscribed to wss://ws-feed.pro.coinbase.com for ['BTC-USD']
        Added item to message collection. Memory Size = (100/1000)
        Added item to message collection. Memory Size = (200/1000)

        >>> websocket.end()
        Unsubscribed from wss://ws-feed.pro.coinbase.com for ['BTC-USD']

    -------
    """
    def __init__(self, 
                 b64_secret_key: str, 
                 api_key: str, 
                 passphrase: str, 
                 products: List[str],
                 channels: List[str],
                 max_memory: int = 1000,
                 sandbox: bool = False, 
                 verbose: bool = True):
        assert isinstance(products, list) and len(products) > 0,\
        "'products' must be a list of products like so ['BTC-USD', ...]"
        
        self.secret_key = b64_secret_key
        self.api_key = api_key
        self.passphrase = passphrase
        self.products = products
        self.sandbox = sandbox
        self.channels = channels
        self.max_memory = max_memory
        
        self.ws = None #websocket
        self.stop = False
        self.thread = None
        self.keepalive = None
        self.verbose = verbose
        self.messages = deque(maxlen=max_memory)
        
        if sandbox:
            self.url = "wss://ws-feed-public.sandbox.exchange.coinbase.com"
        else:
            self.url = "wss://ws-feed.pro.coinbase.com"
            
    def __repr__(self):
        return f"CoinbaseWebSocket(url={self.url}, sandbox={self.sandbox}, products={self.products}, channels={self.channels})"
            
    @classmethod
    def from_file(cls, 
                  filepath: str, 
                  products: List[str],
                  channels: List[str],
                  sandbox: bool) -> WebSocket:
        with open(filepath, "r") as f:
            text = f.read()
            if filepath[-5:] == ".json":
                creds = json.loads(text)
        return cls(b64_secret_key=creds["b64_secret_key"], 
                   api_key=creds["api_key"], 
                   passphrase=creds["passphrase"], 
                   products=products, 
                   channels=channels,
                   sandbox=sandbox)
    
    def start(self, interval: int = 30):
        def flow():
            self.connect()
            self.listen() #will keep running until self.stop = True
            self.kill()
            
        def keep_alive_fn(interval=interval):
            #end the loop once self.stop is True or once we are no longer connected
            while self.ws.connected and not self.stop:
                self.ws.ping("keepalive")
                time.sleep(interval)
        
        self.stop = False
        self.thread = Thread(target=flow)
        self.keepalive = Thread(target=keep_alive_fn)
        self.thread.start() #begin flow -- note self.listen() starts the keepalive thread
        
    def end(self):
        #flips self.stop to True, ending our "listen" loop (see self.listen())
        self.stop = True
        self.keepalive.join() #wait for the "listen" loop to complete
        #self.kill() #this is automatically called by flow after keepalive loop finishes
        #self.thread.join() #wait for the flow to finish -- not needed as will kill it automatically in self.kill
    
    def listen(self):
        self.keepalive.start()
        while not self.stop:
            data = []
            try:
                data = self.ws.recv() #receieve any incoming messages
                data = json.loads(data)
            except Exception as e:
                self.stop = True
                if self.verbose:
                    print(e)
            else: #if no exception in try clause
                self.messages.append(data)
                if self.verbose:
                    mem_len = len(self.messages)
                    if mem_len < self.max_memory and mem_len % 100 == 0:
                        print(f"Added item to message collection. Memory Size = ({len(self.messages)}/{self.max_memory})")
                    elif mem_len == self.max_memory:
                        print(f"Reached memory capacity. Older items will begin dropping off to make room for new ones.")
    
    def connect(self):
        """
        To begin receiving feed messages, you must first send a subscribe message to 
        the server indicating which channels and products to receive.
        docs: https://docs.cloud.coinbase.com/exchange/docs/websocket-channels
        
        To authenticate, send a subscribe message as usual, and pass in fields to GET /users/self/verify, 
        just as if you were signing a request.             
        ---------
        Example (taken from docs)
        ---------
            # Request 
            {"type": "subscribe",
             "product_ids": ["ETH-USD", "BTC-USD"],
             "channels": ["ticker"]}

        """
        params = {"type": "subscribe", "product_ids": self.products}
        if len(self.channels) == 1:
            params.update({"channels": self.channels})
        
        method= "GET"
        endpoint = "/users/self/verify"
        
        timestamp = str(get_timestamp())
        message = "".join([timestamp, method, endpoint])
        
        params["signature"] = sign(message, self.secret_key)
        params["key"] = self.api_key
        params["passphrase"] = self.passphrase
        params["timestamp"] = timestamp

        self.ws = create_connection(self.url)
        self.ws.send(json.dumps(params))
        
        assert self.ws.connected
        if self.verbose:
            print(f"Subscribed to {self.url} for {self.products}")
            
    def kill(self):
        self.ws.close()
        assert not self.ws.connected        
        if self.verbose:
            print(f"Unsubscribed from {self.url} for {self.products}")
        

    


