#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""采集器启动器：初始化并启动所有采集线程"""
import json, time
from logger import info
from config import ADB_ADDRESS
from .base import _local, _adb, _try_local, _start_thread, cmd
from .shared import LOSTAT, _CPU_MAP, _CPU_MAP_PATH, _sd, _auto_save_settings
from . import broadcast, fast_bundle, battery, temperature, memory, storage, ap_ip, processes, cpu


def start() -> None:
    """启动多个独立采集线程，充分利用多核"""
    global _sd
    _startup_ts = time.time()
    _sd["startup_ts"] = _startup_ts
    # 持久化启动时间戳
    try:
        with open(_CPU_MAP_PATH, "r+", encoding="utf-8") as _f:
            _cfg = json.load(_f)
            _cfg["_startup_ts"] = _startup_ts
            _f.seek(0)
            json.dump(_cfg, _f, indent=2, ensure_ascii=False)
            _f.truncate()
    except (OSError, json.JSONDecodeError):
        pass
    cmd(f"adb connect {ADB_ADDRESS}", 5)
    cmd(f"adb -s {ADB_ADDRESS} shell 'echo ADB_READY'", 5)

    # ── 一次性初始化（LOSTAT）──
    if LOSTAT["md"] == "?":
        _init_lostat()
    _sd.update(LOSTAT)

    # ── 共享状态 ──
    cpu_prev = [None]
    net_state = {"rx": 0, "tx": 0, "t": 0}
    _bt_start = [None]

    _start_thread(0.1, lambda: None, "dummy")

    # ── 采集器配置列表: (间隔秒, 函数, 名称, 偏移秒) ──
    _COLLECTORS = [
        (2,  lambda: fast_bundle.collect(cpu_prev, net_state), "fast", 0.0),
        (2,  cpu.collect_freq,                                  "freq", 0.8),
        (10, lambda: battery.collect(_bt_start),                "battery", 0.2),
        (10, temperature.collect,                               "temp", 2.5),
        (10, memory.collect,                                    "mem", 5.0),
        (30, storage.collect,                                   "storage", 3.0),
        (10, ap_ip.collect,                                     "ap", 1.5),
        (10, processes.collect,                                 "proc", 4.0),
        (60, cpu.collect_model,                                 "model", 7.0),
        (30, lambda: _auto_save_settings() or {},               "autosave", 15.0),
    ]

    for interval, fn, name, offset in _COLLECTORS:
        _start_thread(interval, fn, name, offset)

    # ── 广播线程 ──
    broadcast.start()

    info(f"{len(_COLLECTORS)} 个采集线程 + 1 个广播线程已启动")


def _init_lostat() -> None:
    """一次性采集设备静态信息"""
    _man = (_local('getprop ro.product.manufacturer', 2) or "").strip().lower()
    _model = _local('getprop ro.product.model', 2) or ""
    _codename = _local('getprop ro.product.name 2>/dev/null', 2) or _local('getprop ro.product.device 2>/dev/null', 2) or ""
    _man_map = {
        "samsung": "三星", "xiaomi": "小米", "oneplus": "一加", "oppo": "OPPO", "vivo": "vivo",
        "honor": "荣耀", "huawei": "华为", "google": "谷歌", "sony": "索尼", "lg": "LG",
        "motorola": "摩托罗拉", "nokia": "诺基亚", "realme": "真我", "meizu": "魅族",
        "lenovo": "联想", "zte": "中兴", "asus": "华硕", "htc": "宏达电", "nothing": "Nothing",
        "apple": "苹果", "qualcomm": "高通", "mediatek": "联发科",
    }
    _man_cn = _man_map.get(_man, _local('getprop ro.product.manufacturer', 2) or "?")
    _codename_str = f" ({_codename.strip()})" if _codename.strip() and _codename.strip() != _model.strip() else ""
    LOSTAT["md"] = f"{_man_cn} {_model}{_codename_str}"
    LOSTAT["brand"] = _man_cn
    dn = _try_local("settings get global device_name 2>/dev/null",
                    "settings get global device_name 2>/dev/null", 5) or ""
    # 过滤 ADB 错误信息，尝试其他方式获取设备名
    if not dn or "Failure" in dn or "Error" in dn or "exception" in dn.lower():
        dn = _try_local("settings get system device_name 2>/dev/null",
                        "settings get system device_name 2>/dev/null", 3) or ""
    if not dn or "Failure" in dn or "Error" in dn or "exception" in dn.lower():
        dn = _local("getprop ro.product.name 2>/dev/null", 2) or ""
    LOSTAT["dn"] = dn.strip() if dn.strip() else _model or "?"
    LOSTAT["av"] = f"Android {_local('getprop ro.build.version.release', 2) or '?'}"
    LOSTAT["cc"] = _local("ls -d /sys/devices/system/cpu/cpu[0-9]* 2>/dev/null|wc -l", 2) or _local("nproc", 2) or "?"
    _cpu_raw = _local("cat /proc/cpuinfo 2>/dev/null|grep -m1 'Hardware'|cut -d: -f2|xargs", 2) or ""
    if not _cpu_raw:
        _cpu_raw = _local("getprop ro.board.platform 2>/dev/null", 2) or ""
    if not _cpu_raw:
        _cpu_raw = _local("getprop ro.chipname 2>/dev/null", 2) or ""
    if not _cpu_raw:
        _cpu_raw = _local("getprop ro.product.board 2>/dev/null", 2) or ""
    if not _cpu_raw:
        _cpu_raw = _local("getprop ro.hardware 2>/dev/null", 2) or ""
    if not _cpu_raw:
        _cpu_raw = _adb("getprop ro.board.platform 2>/dev/null", 3) or ""
    if not _cpu_raw:
        _cpu_raw = _adb("cat /proc/cpuinfo 2>/dev/null|grep -m1 Hardware|cut -d: -f2|xargs", 5) or ""
    _cpu_impl = _local("grep -m1 'CPU implementer' /proc/cpuinfo 2>/dev/null|cut -d: -f2|xargs", 2) or ""
    LOSTAT["cpu_raw"] = _cpu_raw or "?"
    LOSTAT["cpu_impl"] = _cpu_impl or ""
    info("LOSTAT 初始化完成")
