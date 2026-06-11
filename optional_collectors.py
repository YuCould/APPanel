#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可选采集器模块 — 独立单用途采集函数
======================================

背景
----
APPanel 最初采用「独立采集」架构：每个数据项由单独的线程独立通过 ADB 采集，
各线程并行运行、互不阻塞：

    线程A: _collect_cpu()       → adb shell "cat /proc/stat"
    线程B: _collect_net()       → adb shell "cat /proc/net/dev"
    线程C: _collect_foreground() → adb shell "dumpsys window"

后来优化为「捆绑采集」方案：将 CPU + 网络 + 前台应用合并为单次 ADB 调用，
由 collectors/fast_bundle.py 一个线程完成，减少了 2/3 的 ADB 连接开销。

这些函数已被 `fast_bundle.collect` 替代，当前不由 dashboard.py 启动。
保留在此作为**可选方案**，以便需要更细粒度控制或调试时使用。

使用方式
--------
在 collectors/runner.py 的 start() 中按需替换：

    from optional_collectors import collect_cpu, collect_net, collect_foreground
    from collectors.base import _start_thread

    _start_thread(2, lambda: collect_cpu(cpu_prev), "cpu", offset=0.0)
    _start_thread(2, lambda: collect_net(net_state), "net", offset=0.3)
    _start_thread(2, collect_foreground, "fg", offset=0.6)

各函数签名与原始 _collect_* 完全一致。
"""
import re, time
from config import ADB_ADDRESS
from collectors.base import cmd, _fb, _try_local, _local, _adb
from collectors.shared import LOSTAT, _CPU_MAP, _pkg_label_cache


def collect_cpu(cpu_prev: list) -> dict:
    """采集 CPU 占用率（单次 ADB 调用）"""
    r = cmd(f'adb -s {ADB_ADDRESS} shell "cat /proc/stat|head -1"', 6)
    cs = r.strip()
    if not cs.startswith("cpu"): return {"cr": 0}
    v = [int(x) for x in cs.split()[1:8]]
    t, i = sum(v), v[3]
    d_cr = 0
    if cpu_prev[0]:
        dt, di = t - cpu_prev[0][0], i - cpu_prev[0][1]
        d_cr = round((1 - di / dt) * 100, 1) if dt > 0 else 0
    cpu_prev[0] = (t, i)
    cc = int(LOSTAT.get("cc") or 1)
    return {"cr": d_cr, "cpu_raw": d_cr, "cpu_total": round(d_cr * cc, 1), "cpu": f"{round(d_cr * cc):.0f}%"}


def collect_net(net_state: dict) -> dict:
    """采集网络速率（单次 ADB 调用）"""
    nw = time.time()
    r = cmd(f'adb -s {ADB_ADDRESS} shell "cat /proc/net/dev|grep wlan0"', 6)
    m = re.search(r'wlan0:\s*(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)', r)
    if not m: return {"nr": "0B/s", "nt": "0B/s"}
    nr, nt = int(m.group(1)), int(m.group(2))
    fd = {"nr": "0B/s", "nt": "0B/s"}
    if net_state["t"] > 0 and nr > 0:
        el = nw - net_state["t"]
        if el > 0.5:
            fd["nr"] = _fb(max(0, (nr - net_state["rx"]) / el))
            fd["nt"] = _fb(max(0, (nt - net_state["tx"]) / el))
    net_state.update({"rx": nr, "tx": nt, "t": nw})
    return fd


def collect_cpu_net(cpu_prev: list, net_state: dict) -> dict:
    """CPU + 网络捆绑（单次 ADB 调用）"""
    nw = time.time()
    r = cmd(f'adb -s {ADB_ADDRESS} shell "cat /proc/stat|head -1;echo .;cat /proc/net/dev|grep wlan0"', 6)
    segs = r.split("\n.\n")
    fd = {}
    # CPU
    cs = segs[0].strip() if len(segs) > 0 else ""
    d_cr = 0
    if cs.startswith("cpu"):
        v = [int(x) for x in cs.split()[1:8]]; t, i = sum(v), v[3]
        if cpu_prev[0]:
            dt, di = t - cpu_prev[0][0], i - cpu_prev[0][1]
            d_cr = round((1 - di / dt) * 100, 1) if dt > 0 else 0
        cpu_prev[0] = (t, i)
    fd["cr"] = d_cr
    # 网络
    n = segs[1].strip() if len(segs) > 1 else ""
    m = re.search(r'wlan0:\s*(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)', n)
    if m:
        nr, nt = int(m.group(1)), int(m.group(2))
        if net_state["t"] > 0 and nr > 0:
            el = nw - net_state["t"]
            if el > 0.5:
                fd["nr"] = _fb(max(0, (nr - net_state["rx"]) / el))
                fd["nt"] = _fb(max(0, (nt - net_state["tx"]) / el))
        net_state.update({"rx": nr, "tx": nt, "t": nw})
    if "nr" not in fd: fd["nr"] = "0B/s"
    if "nt" not in fd: fd["nt"] = "0B/s"
    cc = int(LOSTAT.get("cc") or 1)
    fd["cpu_raw"] = d_cr
    fd["cpu_total"] = round(d_cr * cc, 1)
    fd["cpu"] = f"{round(d_cr * cc):.0f}%"
    return fd


def collect_foreground() -> dict:
    """获取当前前台运行的 APP 包名并尝试获取应用名称"""
    shell_cmd = f"dumpsys window 2>/dev/null|grep mCurrentFocus|cut -d/ -f1|awk '{{print $NF}}'"
    r = cmd(f"adb -s {ADB_ADDRESS} shell \"{shell_cmd}\"", 4)
    if not r or r == "?":
        return {"fg": "?", "fg_pkg": "?"}
    _pkg = r.strip().split()[-1] if r.strip() else "?"
    if _pkg.startswith("Window{"): _pkg = _pkg.split()[-1] if len(_pkg.split()) > 1 else "?"
    # 1) 优先 settings.json 映射
    _name = _CPU_MAP["packages"].get(_pkg, "")
    # 2) 查询运行时缓存
    if not _name:
        _name = _pkg_label_cache.get(_pkg, "")
    # 3) 实时查询应用名（adb dumpsys 获取 application-label）
    if not _name:
        _label = cmd(f'adb -s {ADB_ADDRESS} shell "dumpsys package {_pkg} 2>/dev/null|grep -m1 application-label|cut -d: -f2|xargs"', 5)
        _name = _label.strip().strip("'") if _label and _label != "?" else ""
        if _name:
            _pkg_label_cache[_pkg] = _name
    # 4) 兜底：从包名最后一段提取
    if not _name:
        _seg = _pkg.rsplit(".", 1)[-1] if "." in _pkg else _pkg
        _name = _seg if len(_seg) > 1 else _pkg
    return {"fg": _name, "fg_pkg": _pkg}
