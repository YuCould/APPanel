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
            await ws.send(json.dumps(CACHE))
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


def _port_in_use(port: int) -> bool:
    with _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def run() -> None:
    port = FLASK_PORT
    if _port_in_use(port):
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
