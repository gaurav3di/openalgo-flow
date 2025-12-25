"""
WebSocket Client for OpenAlgo real-time data streaming
Provides live LTP, Quotes, and Depth data via WebSocket connection
"""
import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class OpenAlgoWebSocket:
    """
    WebSocket client for OpenAlgo real-time data streaming.

    Supports:
    - LTP (Last Traded Price) streaming
    - Quote streaming (OHLC + volume)
    - Depth streaming (order book)
    """

    def __init__(self, ws_url: str = "ws://127.0.0.1:8765", api_key: str = ""):
        self.ws_url = ws_url
        self.api_key = api_key
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds

        # Subscriptions: {subscription_type: {symbol_key: [callbacks]}}
        self.subscriptions: Dict[str, Dict[str, List[Callable]]] = {
            "ltp": {},
            "quote": {},
            "depth": {}
        }

        # Latest data cache
        self.ltp_cache: Dict[str, float] = {}
        self.quote_cache: Dict[str, Dict] = {}
        self.depth_cache: Dict[str, Dict] = {}

        # Message handlers
        self._message_task: Optional[asyncio.Task] = None
        self._running = False

    def _get_symbol_key(self, exchange: str, symbol: str) -> str:
        """Generate unique key for symbol"""
        return f"{exchange}:{symbol}"

    async def connect(self) -> bool:
        """Connect to OpenAlgo WebSocket server"""
        if self.connected:
            return True

        try:
            logger.info(f"Connecting to OpenAlgo WebSocket: {self.ws_url}")
            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10
            )
            self.connected = True
            self.reconnect_attempts = 0
            self._running = True

            # Start message handler
            self._message_task = asyncio.create_task(self._message_handler())

            logger.info("WebSocket connected successfully")
            return True

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self._running = False

        if self._message_task:
            self._message_task.cancel()
            try:
                await self._message_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()
            self.ws = None

        self.connected = False
        self.subscriptions = {"ltp": {}, "quote": {}, "depth": {}}
        logger.info("WebSocket disconnected")

    async def _message_handler(self):
        """Handle incoming WebSocket messages"""
        while self._running and self.ws:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                await self._process_message(data)

            except ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.connected = False
                await self._try_reconnect()
                break

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")

    async def _process_message(self, data: Dict):
        """Process incoming WebSocket message and notify subscribers"""
        try:
            msg_type = data.get("type", "")

            if msg_type == "ltp":
                await self._handle_ltp(data)
            elif msg_type == "quote":
                await self._handle_quote(data)
            elif msg_type == "depth":
                await self._handle_depth(data)
            elif msg_type == "error":
                logger.error(f"WebSocket error: {data.get('message', 'Unknown error')}")
            elif msg_type == "subscribed":
                logger.debug(f"Subscription confirmed: {data}")
            elif msg_type == "unsubscribed":
                logger.debug(f"Unsubscription confirmed: {data}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_ltp(self, data: Dict):
        """Handle LTP update"""
        exchange = data.get("exchange", "")
        symbol = data.get("symbol", "")
        ltp = data.get("ltp", 0)

        key = self._get_symbol_key(exchange, symbol)
        self.ltp_cache[key] = ltp

        # Notify subscribers
        if key in self.subscriptions["ltp"]:
            for callback in self.subscriptions["ltp"][key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(exchange, symbol, ltp, data)
                    else:
                        callback(exchange, symbol, ltp, data)
                except Exception as e:
                    logger.error(f"LTP callback error: {e}")

    async def _handle_quote(self, data: Dict):
        """Handle Quote update"""
        exchange = data.get("exchange", "")
        symbol = data.get("symbol", "")

        key = self._get_symbol_key(exchange, symbol)
        self.quote_cache[key] = data

        # Also update LTP cache
        if "ltp" in data:
            self.ltp_cache[key] = data["ltp"]

        # Notify subscribers
        if key in self.subscriptions["quote"]:
            for callback in self.subscriptions["quote"][key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(exchange, symbol, data)
                    else:
                        callback(exchange, symbol, data)
                except Exception as e:
                    logger.error(f"Quote callback error: {e}")

    async def _handle_depth(self, data: Dict):
        """Handle Depth update"""
        exchange = data.get("exchange", "")
        symbol = data.get("symbol", "")

        key = self._get_symbol_key(exchange, symbol)
        self.depth_cache[key] = data

        # Notify subscribers
        if key in self.subscriptions["depth"]:
            for callback in self.subscriptions["depth"][key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(exchange, symbol, data)
                    else:
                        callback(exchange, symbol, data)
                except Exception as e:
                    logger.error(f"Depth callback error: {e}")

    async def _try_reconnect(self):
        """Attempt to reconnect to WebSocket"""
        while self.reconnect_attempts < self.max_reconnect_attempts and self._running:
            self.reconnect_attempts += 1
            logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")

            await asyncio.sleep(self.reconnect_delay)

            if await self.connect():
                # Resubscribe to all symbols
                await self._resubscribe_all()
                return

        logger.error("Max reconnection attempts reached")

    async def _resubscribe_all(self):
        """Resubscribe to all previously subscribed symbols"""
        for sub_type, symbols in self.subscriptions.items():
            for key in symbols.keys():
                exchange, symbol = key.split(":")
                await self._send_subscribe(sub_type, exchange, symbol)

    async def _send_subscribe(self, sub_type: str, exchange: str, symbol: str):
        """Send subscription message"""
        if not self.connected or not self.ws:
            return False

        message = {
            "action": "subscribe",
            "type": sub_type,
            "instruments": [{"exchange": exchange, "symbol": symbol}]
        }

        try:
            await self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send subscribe: {e}")
            return False

    async def _send_unsubscribe(self, sub_type: str, exchange: str, symbol: str):
        """Send unsubscription message"""
        if not self.connected or not self.ws:
            return False

        message = {
            "action": "unsubscribe",
            "type": sub_type,
            "instruments": [{"exchange": exchange, "symbol": symbol}]
        }

        try:
            await self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send unsubscribe: {e}")
            return False

    # =========================================================================
    # Public API - LTP
    # =========================================================================

    async def subscribe_ltp(
        self,
        exchange: str,
        symbol: str,
        callback: Callable
    ) -> bool:
        """
        Subscribe to LTP updates for a symbol.

        Args:
            exchange: Exchange code (NSE, BSE, NFO, etc.)
            symbol: Trading symbol
            callback: Function called on LTP update: callback(exchange, symbol, ltp, data)

        Returns:
            True if subscription successful
        """
        key = self._get_symbol_key(exchange, symbol)

        if key not in self.subscriptions["ltp"]:
            self.subscriptions["ltp"][key] = []
            # First subscriber, send subscribe message
            if self.connected:
                await self._send_subscribe("ltp", exchange, symbol)

        if callback not in self.subscriptions["ltp"][key]:
            self.subscriptions["ltp"][key].append(callback)

        return True

    async def unsubscribe_ltp(
        self,
        exchange: str,
        symbol: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        Unsubscribe from LTP updates.

        Args:
            exchange: Exchange code
            symbol: Trading symbol
            callback: Specific callback to remove, or None to remove all
        """
        key = self._get_symbol_key(exchange, symbol)

        if key not in self.subscriptions["ltp"]:
            return True

        if callback:
            if callback in self.subscriptions["ltp"][key]:
                self.subscriptions["ltp"][key].remove(callback)
        else:
            self.subscriptions["ltp"][key] = []

        # If no more subscribers, unsubscribe from server
        if not self.subscriptions["ltp"][key]:
            del self.subscriptions["ltp"][key]
            if self.connected:
                await self._send_unsubscribe("ltp", exchange, symbol)

        return True

    def get_ltp(self, exchange: str, symbol: str) -> Optional[float]:
        """Get cached LTP for a symbol"""
        key = self._get_symbol_key(exchange, symbol)
        return self.ltp_cache.get(key)

    # =========================================================================
    # Public API - Quote
    # =========================================================================

    async def subscribe_quote(
        self,
        exchange: str,
        symbol: str,
        callback: Callable
    ) -> bool:
        """Subscribe to Quote updates (OHLC + volume)"""
        key = self._get_symbol_key(exchange, symbol)

        if key not in self.subscriptions["quote"]:
            self.subscriptions["quote"][key] = []
            if self.connected:
                await self._send_subscribe("quote", exchange, symbol)

        if callback not in self.subscriptions["quote"][key]:
            self.subscriptions["quote"][key].append(callback)

        return True

    async def unsubscribe_quote(
        self,
        exchange: str,
        symbol: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """Unsubscribe from Quote updates"""
        key = self._get_symbol_key(exchange, symbol)

        if key not in self.subscriptions["quote"]:
            return True

        if callback:
            if callback in self.subscriptions["quote"][key]:
                self.subscriptions["quote"][key].remove(callback)
        else:
            self.subscriptions["quote"][key] = []

        if not self.subscriptions["quote"][key]:
            del self.subscriptions["quote"][key]
            if self.connected:
                await self._send_unsubscribe("quote", exchange, symbol)

        return True

    def get_quote(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get cached Quote for a symbol"""
        key = self._get_symbol_key(exchange, symbol)
        return self.quote_cache.get(key)

    # =========================================================================
    # Public API - Depth
    # =========================================================================

    async def subscribe_depth(
        self,
        exchange: str,
        symbol: str,
        callback: Callable
    ) -> bool:
        """Subscribe to Depth updates (order book)"""
        key = self._get_symbol_key(exchange, symbol)

        if key not in self.subscriptions["depth"]:
            self.subscriptions["depth"][key] = []
            if self.connected:
                await self._send_subscribe("depth", exchange, symbol)

        if callback not in self.subscriptions["depth"][key]:
            self.subscriptions["depth"][key].append(callback)

        return True

    async def unsubscribe_depth(
        self,
        exchange: str,
        symbol: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """Unsubscribe from Depth updates"""
        key = self._get_symbol_key(exchange, symbol)

        if key not in self.subscriptions["depth"]:
            return True

        if callback:
            if callback in self.subscriptions["depth"][key]:
                self.subscriptions["depth"][key].remove(callback)
        else:
            self.subscriptions["depth"][key] = []

        if not self.subscriptions["depth"][key]:
            del self.subscriptions["depth"][key]
            if self.connected:
                await self._send_unsubscribe("depth", exchange, symbol)

        return True

    def get_depth(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get cached Depth for a symbol"""
        key = self._get_symbol_key(exchange, symbol)
        return self.depth_cache.get(key)


# Global WebSocket client instance
_ws_client: Optional[OpenAlgoWebSocket] = None


def get_websocket_client() -> Optional[OpenAlgoWebSocket]:
    """Get the global WebSocket client instance"""
    return _ws_client


async def initialize_websocket(ws_url: str, api_key: str) -> OpenAlgoWebSocket:
    """Initialize the global WebSocket client"""
    global _ws_client

    if _ws_client:
        await _ws_client.disconnect()

    _ws_client = OpenAlgoWebSocket(ws_url=ws_url, api_key=api_key)
    await _ws_client.connect()

    return _ws_client


async def shutdown_websocket():
    """Shutdown the global WebSocket client"""
    global _ws_client

    if _ws_client:
        await _ws_client.disconnect()
        _ws_client = None
