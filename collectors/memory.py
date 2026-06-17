#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内存采集（原始 KB 值）"""
from .base import _adb_mem


def collect() -> dict:
    """读取 /proc/meminfo 原始 KB 值（走独立 mem 通道）"""
    mr = _adb_mem("cat /proc/meminfo|head -5", 3)
    mt = ma = 0
    for l in mr.split("\n"):
        if "MemTotal:" in l:
            mt = int(l.split()[1])
        if "MemAvailable:" in l:
            ma = int(l.split()[1])
    if mt == 0:
        return {}
    return {
        "mem_kb": mt,       # 总内存 KB
        "mem_avail_kb": ma,  # 可用内存 KB
    }
