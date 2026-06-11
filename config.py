#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APPanel 全局配置
所有硬编码地址、端口集中管理，一处修改全局生效。
"""

# ── ADB 连接 ──
ADB_HOST: str = "127.0.0.1"
ADB_PORT: int = 5555
ADB_ADDRESS: str = f"{ADB_HOST}:{ADB_PORT}"  # "127.0.0.1:5555"

def adb_cmd(cmd_str: str) -> str:
    """生成带 ADB 地址的 shell 命令前缀"""
    return f"adb -s {ADB_ADDRESS} shell \"{cmd_str}\""

# ── 网络服务 ──
HOST: str = "0.0.0.0"
WS_PORT: int = 5001          # WebSocket 广播端口
FLASK_PORT: int = 80         # Flask 主端口
FLASK_FALLBACK_PORT: int = 20080  # Flask 备用端口

# ── AP 后端检测 ──
AP_HOST: str = "127.0.0.1"
AP_PORT: int = 22267
