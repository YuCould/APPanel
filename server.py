#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APPanel 服务器模块
"""
import asyncio, json, threading, socket as _sk, logging
from flask import Flask
import websockets

from config import HOST, WS_PORT, FLASK_PORT, FLASK_FALLBACK_PORT
from collectors.ws import WS_CLIENTS, CACHE
from routes import register_all

app = Flask(__name__)
register_all(app)

# 抑制 Werkzeug 开发服务器警告
logging.getLogger('werkzeug').setLevel(logging.ERROR)


async def ws_handler(ws) -> None:
    WS_CLIENTS.add(ws)
    try:
        if CACHE:
            from collectors.shared import _CPU_MAP
            payload = dict(CACHE)
            payload["_pkg_map"] = _CPU_MAP.get("packages", {})
            payload["_hidden_procs"] = _CPU_MAP.get("hidden_procs", {})
            try:
                from collectors.adb_shell import get_channel_adb_pids, get_channel_local_pids
                payload["_adb_pids"] = get_channel_adb_pids()
                payload["_local_pids"] = get_channel_local_pids()
            except Exception:
                pass
            await ws.send(json.dumps(payload))
        async for msg in ws:
            try:
                data = json.loads(msg)
                pass
            except json.JSONDecodeError:
                pass
    finally:
        WS_CLIENTS.discard(ws)



async def ws_server() -> None:
    async with websockets.serve(ws_handler, HOST, WS_PORT, compression=None):
        await asyncio.Future()


def start_ws() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_server())


def run() -> None:
    port = FLASK_PORT
    # 先尝试绑定（含 SO_REUSEADDR 解决重启后 TIME_WAIT）
    try:
        with _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM) as s:
            s.setsockopt(_sk.SOL_SOCKET, _sk.SO_REUSEADDR, 1)
            s.bind((HOST, port))
            s.close()
    except (OSError, PermissionError):
        port = FLASK_FALLBACK_PORT
    else:
        with _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                s.close()
            except (OSError, PermissionError):
                port = FLASK_FALLBACK_PORT
                print(f"[SERVER] port {FLASK_PORT} no permission, fallback to {port}")
    app.run(host=HOST, port=port, debug=False)
