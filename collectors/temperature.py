#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CPU 温度采集（原始 millidegree）"""
from .base import _local_medium, _adb_medium


def collect() -> dict:
    """遍历 thermal_zone 读取 CPU 温度原始值"""
    _CMD = ("for z in 6 79 5 7 10 11 1 0; do "
            "v=$(cat /sys/class/thermal/thermal_zone$z/temp 2>/dev/null) && "
            "[ \"$v\" -gt 0 ] 2>/dev/null && echo \"$v\" && break; done")
    r = _local_medium(_CMD, 2)
    if not r.strip().isdigit():
        r = _adb_medium(_CMD, 2)
    if r.strip().isdigit() and int(r.strip()) > 0:
        return {"ct_raw": int(r.strip())}  # millidegree，如 70000 = 70.0°C
    return {}
