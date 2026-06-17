#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速采集：CPU jiffies + 网络字节数 + AP进程资源（fast 通道）"""
import re
from .base import _adb_fast, _local_fast


# 网络初始基线（服务端持久化，所有 WS 客户端共享同一总量）
_net_base = {"rx0": None, "tx0": None}


def collect() -> dict:
    """快速采集 CPU jiffies + 网络字节数 + 网络总量"""
    global _net_base
    raw = _adb_fast("cat /proc/stat|head -1;echo .;cat /proc/net/dev|grep wlan0", 6)
    segments = raw.split("\n.\n")
    result = {}

    # ── CPU 原始 jiffies ──
    cpu_line = segments[0].strip() if len(segments) > 0 else ""
    if cpu_line.startswith("cpu"):
        parts = cpu_line.split()
        if len(parts) >= 8:
            result["cpu_jiffies"] = " ".join(parts[1:8])

    # ── 网络原始字节数 + 总量（服务端计算，所有客户端一致）──
    net_line = segments[1].strip() if len(segments) > 1 else ""
    net_match = re.search(r'wlan0:\s*(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)', net_line)
    if net_match:
        rx = int(net_match.group(1))
        tx = int(net_match.group(2))
        result["net_rx"] = rx
        result["net_tx"] = tx
        # 首次运行记录基线
        if _net_base["rx0"] is None:
            _net_base["rx0"] = rx
            _net_base["tx0"] = tx
        # 总量（相对于基线的差值）
        result["net_rx_total"] = rx - _net_base["rx0"]
        result["net_tx_total"] = tx - _net_base["tx0"]

    # ── AP 进程资源（轻量，合并到快速采集）──
    try:
        ps_out = _local_fast("ps --no-headers -eo pid,%cpu,%mem,cmd 2>/dev/null | grep 'gui.py'", 3)
        for line in ps_out.split("\n"):
            line = line.strip()
            if not line or "grep" in line:
                continue
            parts = line.split()
            if len(parts) >= 4 and "gui.py" in parts[3]:
                result["ap_pid"] = int(parts[0])
                result["ap_cpu"] = parts[1]
                result["ap_mem"] = parts[2]
                break
    except Exception:
        pass

    return result
