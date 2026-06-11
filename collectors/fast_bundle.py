#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""捆绑采集：CPU + 网络 + 前台应用（单次 ADB 调用）"""
import re, time
from config import ADB_ADDRESS
from .base import cmd, _fb, _try_local
from .shared import _CPU_MAP, LOSTAT, _pkg_label_cache, _mark_dirty, SYS_PREFIXES


def collect(cpu_prev: list, net_state: dict) -> dict:
    """快速捆绑采集：CPU + 网络 + 前台（单次 ADB 调用）"""
    now = time.time()
    fg_query = "dumpsys window 2>/dev/null|grep mCurrentFocus|cut -d/ -f1|awk '{{print $NF}}'"
    raw_output = cmd(f"adb -s {ADB_ADDRESS} shell \"cat /proc/stat|head -1;echo .;cat /proc/net/dev|grep wlan0;echo .;{fg_query}\"", 6)
    segments = raw_output.split("\n.\n")
    result = {}
    # ── CPU ──
    cpu_line = segments[0].strip() if len(segments) > 0 else ""
    cpu_ratio = 0
    if cpu_line.startswith("cpu"):
        cpu_values = [int(x) for x in cpu_line.split()[1:8]]
        total_time, idle_time = sum(cpu_values), cpu_values[3]
        if cpu_prev[0]:
            delta_total = total_time - cpu_prev[0][0]
            delta_idle = idle_time - cpu_prev[0][1]
            cpu_ratio = round((1 - delta_idle / delta_total) * 100, 1) if delta_total > 0 else 0
        cpu_prev[0] = (total_time, idle_time)
    result["cr"] = cpu_ratio
    # ── 网络 ──
    net_line = segments[1].strip() if len(segments) > 1 else ""
    net_match = re.search(r'wlan0:\s*(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)', net_line)
    if net_match:
        net_rx, net_tx = int(net_match.group(1)), int(net_match.group(2))
        # 首次记录初始值
        if net_state.get("rx0") is None:
            net_state["rx0"] = net_rx
            net_state["tx0"] = net_tx
        # 总流量（自启动以来的累计）
        result["net_rx_total"] = net_rx - net_state["rx0"]
        result["net_tx_total"] = net_tx - net_state["tx0"]
        if net_state["t"] > 0 and net_rx > 0:
            elapsed = now - net_state["t"]
            if elapsed > 0.5:
                result["nr"] = _fb(max(0, (net_rx - net_state["rx"]) / elapsed))
                result["nt"] = _fb(max(0, (net_tx - net_state["tx"]) / elapsed))
        net_state.update({"rx": net_rx, "tx": net_tx, "t": now})
    if "nr" not in result:
        result["nr"] = "0B/s"
    if "nt" not in result:
        result["nt"] = "0B/s"
    core_count = int(LOSTAT.get("cc") or 1)
    result["cpu_raw"] = cpu_ratio
    result["cpu_total"] = round(cpu_ratio * core_count, 1)
    result["cpu"] = f"{round(cpu_ratio * core_count):.0f}%"
    # ── 前台应用 ──
    fg_raw = segments[2].strip() if len(segments) > 2 else ""
    pkg_name = fg_raw.split()[-1] if fg_raw else "?"
    if pkg_name.startswith("Window{"):
        pkg_name = pkg_name.split()[-1] if len(pkg_name.split()) > 1 else "?"
    app_name = _CPU_MAP["packages"].get(pkg_name, "") or _pkg_label_cache.get(pkg_name, "")
    if not app_name and pkg_name and pkg_name != "?":
        pkg_query = f"dumpsys package {pkg_name} 2>/dev/null|grep -m1 application-label|cut -d: -f2|xargs"
        app_label = _try_local(pkg_query, pkg_query, 5)
        app_name = app_label.strip().strip("'") if app_label and app_label != "?" else ""
        if app_name:
            _pkg_label_cache[pkg_name] = app_name
    if not app_name:
        name_segment = pkg_name.rsplit(".", 1)[-1] if "." in pkg_name else pkg_name
        app_name = name_segment if len(name_segment) > 1 else pkg_name
        if (pkg_name.count(".") >= 2 and pkg_name not in _CPU_MAP["packages"]
                and not any(pkg_name.startswith(p) for p in SYS_PREFIXES)):
            _CPU_MAP["packages"][pkg_name] = app_name
            _mark_dirty()
    result["fg"] = app_name or "?"
    result["fg_pkg"] = pkg_name
    return result
