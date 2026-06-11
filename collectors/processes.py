#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""进程列表采集 + 应用名解析"""
from config import ADB_ADDRESS
from .base import cmd
from .shared import _CPU_MAP, _pkg_label_cache, _mark_dirty, SYS_PREFIXES


def _resolve_app_name(pkg_name: str) -> str:
    """从包名解析应用名称（精确匹配→前缀匹配→缓存→自动学习→兜底）"""
    executable = pkg_name.split()[0].split("/")[-1]
    resolved = _CPU_MAP["packages"].get(executable, "")
    if resolved:
        return resolved
    base_pkg = pkg_name.split(":")[0]
    if "." not in base_pkg:
        return ""
    # 精确匹配
    resolved = _CPU_MAP["packages"].get(base_pkg, "")
    if resolved:
        return resolved
    # 前缀匹配
    parts = base_pkg.split(".")
    for i in range(len(parts) - 1, 1, -1):
        prefix = ".".join(parts[:i])
        resolved = _CPU_MAP["packages"].get(prefix, "")
        if resolved:
            return resolved
    # 运行时缓存
    resolved = _pkg_label_cache.get(base_pkg, "")
    if resolved:
        return resolved
    # 自动学习
    is_system = any(base_pkg.startswith(p) for p in SYS_PREFIXES) or parts[-1] in ("system", "core", "service", "provider")
    if not is_system and len(parts) >= 3:
        name_segment = parts[-1] if len(parts[-1]) > 1 else parts[-2]
        _CPU_MAP["packages"][base_pkg] = name_segment
        _mark_dirty()
        return name_segment
    # 兜底
    name_segment = base_pkg.rsplit(".", 1)[-1]
    return name_segment if len(name_segment) > 1 else ""


def collect() -> dict:
    """采集进程列表（CPU > 0.2% 过滤）"""
    processes = []
    for line in cmd(f"adb -s {ADB_ADDRESS} shell \"ps -e -o pid,pcpu,rss,args 2>/dev/null\"", 5).split(chr(10)):
        fields = line.split()
        if len(fields) >= 4 and fields[0].isdigit() and int(fields[0]) > 0:
            proc_name = " ".join(fields[3:])[:80] if len(fields) > 3 else fields[3][:80]
            if proc_name.startswith("["):
                continue
            # 解析内存
            rss_raw = fields[2]
            if rss_raw.isdigit():
                rss_kb = int(rss_raw)
                rss_display = f"{rss_kb / 1024:.1f}M" if rss_kb >= 1024 else f"{rss_kb}K"
            elif rss_raw.endswith("M"):
                rss_display = rss_raw
            elif rss_raw.endswith("K"):
                rss_display = f"{float(rss_raw[:-1]) / 1024:.1f}M"
            elif rss_raw.endswith("G"):
                rss_display = f"{float(rss_raw[:-1]) * 1024:.0f}M"
            else:
                rss_display = rss_raw or "0"
            # 统一为 MB 数值用于排序
            rss_mb = rss_display
            if rss_mb.endswith("K"):
                mem_mb = round(float(rss_mb[:-1]) / 1024, 1)
            elif rss_mb.endswith("M"):
                mem_mb = float(rss_mb[:-1])
            elif rss_mb.endswith("G"):
                mem_mb = float(rss_mb[:-1]) * 1024
            else:
                mem_mb = 0
            if float(fields[1]) > 0.2:
                # 过滤采集自身进程
                self_prefixes = ["adb ", "adb-", "adbd ", "sh -c ps", "ps -e -o pid", "adb fork-server", "adb -L"]
                if any(proc_name.startswith(x) for x in self_prefixes):
                    continue
                adb_tools = ["dumpsys", "procrank", "procmem"]
                if any(x in proc_name for x in adb_tools):
                    app_name = "APPanel"
                else:
                    app_name = _resolve_app_name(proc_name)
                    # Python 子进程（带参数）显示为 py
                    base = proc_name.split()[0] if proc_name else ""
                    if app_name == "APPanel" and base in ("python", "python3") and len(proc_name.split()) > 1:
                        app_name = "py"
                processes.append({
                    "p": fields[0], "u": "?", "c": fields[1],
                    "m": rss_display, "mn": mem_mb,
                    "n": proc_name[:30], "cl": proc_name, "an": app_name,
                })
    # 注入 APPanel 自身进程信息（确保始终可见）
    import os as _os
    _self_pid = _os.getpid()
    # 检查是否已在列表中
    if not any(p["p"] == str(_self_pid) for p in processes):
        try:
            _self_rss = int(cmd(f"cat /proc/{_self_pid}/status 2>/dev/null|grep VmRSS|awk '{{print $2}}'", 2) or "0")
            _self_mem = f"{_self_rss / 1024:.1f}M" if _self_rss else "0K"
            # 假 CPU 设为 0.5 确保排序时可见，但不影响整体排序
            processes.append({
                "p": str(_self_pid), "u": "?", "c": "0.5",
                "m": _self_mem, "mn": round(_self_rss / 1024, 1) if _self_rss else 0,
                "n": "dashboard.py", "cl": "dashboard.py", "an": "APPanel",
            })
        except Exception:
            processes.append({
                "p": str(_self_pid), "u": "?", "c": "0.5",
                "m": "0K", "mn": 0,
                "n": "dashboard.py", "cl": "dashboard.py", "an": "APPanel",
            })
    return {"pr": processes}
