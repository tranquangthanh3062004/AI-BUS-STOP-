"""
sync_service/network_monitor.py
Background Network Health Monitor for Smart Bus Stop Kiosk.
Periodically checks internet connectivity (ping / TCP connect) to enable automatic failover between Online and Offline modes.
"""

import asyncio
import socket
from shared.config import settings
from shared.logger import logger


class NetworkMonitor:
    def __init__(self, host: str = None, port: int = 53, interval_sec: int = None, timeout_sec: float = None):
        self.host = host or settings.ping_target_host
        self.port = port
        self.interval_sec = interval_sec or settings.ping_interval_sec
        self.timeout_sec = timeout_sec or settings.ping_timeout_sec
        self.is_online = False
        self._running = False
        self._task = None

    async def check_connectivity(self) -> bool:
        """
        Fast TCP socket check to verify internet connectivity using Asyncio.
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout_sec
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _monitor_loop(self, state_dict: dict = None):
        logger.info(f"NetworkMonitor background service started. Monitoring {self.host}:{self.port} every {self.interval_sec}s.")
        while self._running:
            status = await self.check_connectivity()
            if status != self.is_online:
                self.is_online = status
                logger.info(f"Network status changed! Real Connectivity: {'ONLINE' if status else 'OFFLINE'}")
                if state_dict is not None and not state_dict.get("manual_override", False):
                    state_dict["network_mode"] = "ONLINE" if status else "OFFLINE"
                    state_dict["last_ping_status"] = status
            await asyncio.sleep(self.interval_sec)

    def start(self, state_dict: dict = None):
        if self._running:
            return
        self._running = True
        self.is_online = True  # Assume online initially, let monitor loop update it
        if state_dict is not None:
            # Set ONLINE immediately on startup so first requests use online pipeline
            state_dict["network_mode"] = "ONLINE"
            state_dict["last_ping_status"] = self.is_online
        self._task = asyncio.create_task(self._monitor_loop(state_dict))

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
