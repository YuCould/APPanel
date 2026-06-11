#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 广播模块
持有广播缓存 CACHE、客户端集合 WS_CLIENTS、广播函数 ws_broadcast。
"""
import json, asyncio

# 广播缓存（采集器写入 → 广播线程读取 → WebSocket 推送）
CACHE: dict = {}

# 已连接的 WebSocket 客户端集合
WS_CLIENTS: set = set()


async def ws_broadcast(data: dict) -> None:
    """向所有已连接的 WebSocket 客户端广播数据"""
    if WS_CLIENTS:
        msg = json.dumps(data)
        await asyncio.gather(*[c.send(msg) for c in WS_CLIENTS], return_exceptions=True)
