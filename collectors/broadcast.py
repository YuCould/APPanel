#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广播线程模块
定期将采集数据从 _sd 同步到 CACHE 并通过 WebSocket 推送。
"""
import asyncio, threading, time
from .shared import _sd, _data_lock
from .ws import CACHE, ws_broadcast


def start() -> None:
    """在后台线程中启动广播循环（每 0.1 秒推送一次）"""

    def _loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            try:
                with _data_lock:
                    if _sd:
                        CACHE.clear()
                        CACHE.update(_sd)
                if CACHE:
                    loop.run_until_complete(ws_broadcast(CACHE))
                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)

    threading.Thread(target=_loop, daemon=True).start()
