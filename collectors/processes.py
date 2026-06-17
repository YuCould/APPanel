#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""进程列表采集（原始 ps 输出，后端按 hidden_procs 过滤）"""
import os as _os
from .base import _adb_proc, cmd
from .shared import _CPU_MAP
from .adb_shell import get_channel_local_pids


def collect() -> dict:
    """采集原始 ps 列表，过滤隐藏进程，注入后端自身进程信息和本地 shell 进程"""
    raw = _adb_proc("ps -e -o pid,pcpu,rss,args 2>/dev/null", 5)
    # 后端过滤隐藏进程（降低 ps_raw 大小，减少网络传输）
    hidden = _CPU_MAP.get("hidden_procs", {})
    if hidden and raw:
        lines = raw.split("\n")
        filtered = []
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            # 取 args 部分（第4列之后）
            parts = line_stripped.split(None, 3)
            if len(parts) < 4:
                filtered.append(line_stripped)
                continue
            args = parts[3]
            skip = False
            for prefix in hidden:
                if args.startswith(prefix) or ("/" + prefix) in args:
                    skip = True
                    break
            if not skip:
                filtered.append(line_stripped)
        raw = "\n".join(filtered)
    result = {"ps_raw": raw}
    # 注入 APPanel 自身进程（在 Termux 本地）
    self_pid = _os.getpid()
    self_rss = 0
    try:
        r = cmd(f"cat /proc/{self_pid}/status 2>/dev/null|grep VmRSS|awk '{{print $2}}'", 2)
        if r and r.strip().isdigit():
            self_rss = int(r.strip())
    except Exception:
        pass
    result["self_pid"] = self_pid
    result["self_rss_kb"] = self_rss

    # 采集各通道本地 bash --norc 进程信息（独立字段，不混入 ps_raw）
    _bash_procs = {}
    for _ch, _pid in get_channel_local_pids().items():
        _rss = 0
        try:
            _r = cmd(f"cat /proc/{_pid}/status 2>/dev/null|grep VmRSS|awk '{{print $2}}'", 2)
            if _r and _r.strip().isdigit():
                _rss = int(_r.strip())
        except Exception:
            pass
        _bash_procs[_ch] = {"pid": _pid, "rss_kb": _rss}
    result["_bash_procs"] = _bash_procs
    return result
