"""
-----------
Coinbase Pro API Wrappers
-----------
Suggested use (to remove the risk of ambiguity with other imported modules):
    >>> import coinbase
    >>> coinbase.Public() #for public api
    >>> coinbase.Private() #for private api
    >>> coinbase.WebSocket() #for websocket
-----------
"""

from .api import Public, Private
from .websocket import WebSocket
