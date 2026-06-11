#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内存采集（从 /proc/meminfo 读取，本地失败回退 ADB）"""
from .base import _try_local


def collect() -> dict:
    """读取内存总量与可用量"""
    _CMD = "cat /proc/meminfo|head -5"
    mr = _try_local(_CMD, _CMD, 3)
    mt = ma = 0
    for l in mr.split("\n"):
        if "MemTotal:" in l:
            mt = int(l.split()[1])
        if "MemAvailable:" in l:
            ma = int(l.split()[1])
    if mt == 0:
        return {"mp": 0, "mt": "?", "mu": "?", "ma": "?"}
    return {
        "mp": round((mt - ma) / mt * 100, 1),
        "mt": f"{mt // 1024}MB",
        "mu": f"{(mt - ma) // 1024}MB",
        "ma": f"{ma // 1024}MB",
    }
