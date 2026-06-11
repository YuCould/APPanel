#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CPU 温度采集（从 thermal_zone 读取，本地失败回退 ADB）"""
from .base import _try_local


def collect() -> dict:
    """遍历 thermal_zone 读取 CPU 温度"""
    _CMD = ("for z in 6 79 5 7 10 11 1 0; do "
            "v=$(cat /sys/class/thermal/thermal_zone$z/temp 2>/dev/null) && "
            "[ \"$v\" -gt 0 ] 2>/dev/null && echo \"$v\" && break; done")
    r = _try_local(_CMD, _CMD, 2)
    if r.strip().isdigit() and int(r.strip()) > 0:
        return {"ct": f"{int(r.strip()) / 1000:.1f}°C"}
    return {"ct": ""}
