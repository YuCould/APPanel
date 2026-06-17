#./,/r,,,n/env py.,.n3,,,.,.,..,./,,,,..,..,,,,...
# -*- coding: utf-8 -*-
"""
APPanel 全局配置
端口值从 settings.json 读取（Web 页面编辑保存）。
"""
import os, json

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def _load_port_overrides() -> dict:
    overrides = {}
    try:
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            for k in ("flask_port", "ws_port", "ap_port", "adb_port", "screen_port"):
                v = data.get(k)
                if v is not None:
                    overrides[k] = v
    except Exception:
        pass
    return overrides

_port_overrides = _load_port_overrides()

# ── ADB 连接 ──
ADB_HOST: str = "127.0.0.1"
ADB_PORT: int = _port_overrides.get("adb_port") or 5555
ADB_ADDRESS: str = f"{ADB_HOST}:{ADB_PORT}"  # "127.0.0.1:5555"

def adb_cmd(cmd_str: str) -> str:
    """生成带 ADB 地址的 shell 命令前缀"""
    return f"adb -s {ADB_ADDRESS} shell \"{cmd_str}\""

# ── 网络服务 ──
HOST: str = "0.0.0.0"
WS_PORT: int = _port_overrides.get("ws_port") or 5001          # WebSocket 广播端口
FLASK_PORT: int = _port_overrides.get("flask_port") or 80       # Flask 主端口
FLASK_FALLBACK_PORT: int = 20080                                # Flask 备用端口

# ── AP 后端检测 ──
AP_HOST: str = "127.0.0.1"
AP_PORT: int = _port_overrides.get("ap_port") or 22267
