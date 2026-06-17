#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""采集器启动器：初始化并启动所有采集线程"""
import json, time
from logger import info
from config import ADB_ADDRESS
from .base import _local, _adb, _local_fast, _adb_fast, _local_freq, _adb_freq, _local_mem, _adb_mem, _local_proc, _adb_proc, _local_medium, _adb_medium, _local_slow, _adb_slow, _local_ap, _adb_ap, _try_local, _start_thread, cmd
from .shared import LOSTAT, _CPU_MAP, _CPU_MAP_PATH, _sd, _auto_save_settings
from . import adb_shell, broadcast, fast_bundle, battery, temperature, memory, storage, ap_ip, processes, cpu, hot_protect


def start() -> None:
    """启动持久 shell + 多个独立采集线程"""
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

    # ── 启动持久 ADB shell ──
    cmd(f"adb connect {ADB_ADDRESS}", 5)
    adb_shell.start()
    # 验证 ADB shell 可用
    _adb("echo ADB_READY", 5)
    info("持久 ADB shell 就绪")

    # ── 一次性初始化（LOSTAT）──
    if LOSTAT["md"] == "?":
        _init_lostat()
    _sd.update(LOSTAT)

    # ── 各通道采集速度倍率 ──
    _speeds = _CPU_MAP.get("collect_speeds", {})
    _speed_map = {
        "fast":   max(0.1, float(_speeds.get("fast", 1.0))),
        "freq":   max(0.1, float(_speeds.get("fast", 1.0))),
        "mem":    max(0.1, float(_speeds.get("fast", 1.0))),
        "proc":   max(0.1, float(_speeds.get("fast", 1.0))),
        "medium": max(0.1, float(_speeds.get("medium", 1.0))),
        "slow":   max(0.1, float(_speeds.get("slow", 1.0))),
        "ap":     max(0.1, float(_speeds.get("slow", 1.0))),
    }
    info(f"采集速度倍率: fast={_speed_map['fast']}x medium={_speed_map['medium']}x slow={_speed_map['slow']}x")

    # ── 采集器配置列表: (基础间隔秒, 函数, 名称, 偏移秒, 通道) ──
    # 实际间隔 = 基础间隔 * 对应通道的速度倍率
    _BASE_COLLECTORS = [
        # ── 各通道独立，消除锁竞争 ──
        (2,  fast_bundle.collect,                                "cpu+net", 0.0,  "fast"),
        (2,  cpu.collect_freq,                                   "freq",    0.8,  "freq"),
        (2,  memory.collect,                                     "mem",     5.0,  "mem"),
        (2,  processes.collect,                                  "proc",    4.0,  "proc"),
        # ── 中速（medium 通道）──
        (10, battery.collect,                                    "battery", 0.2,  "medium"),
        (10, temperature.collect,                                "temp",    2.5,  "medium"),
        # ── 慢速（slow/ap 通道）──
        (30, storage.collect,                                    "storage", 3.0,  "slow"),
        (10, ap_ip.collect,                                      "ap",      1.5,  "ap"),
        (60, cpu.collect_model,                                  "model",   7.0,  "ap"),
        (30, lambda: _auto_save_settings() or {},                "autosave",15.0, "ap"),
    ]

    for base_interval, fn, name, offset, ch in _BASE_COLLECTORS:
        adjusted = base_interval * _speed_map.get(ch, 1.0)
        _start_thread(adjusted, fn, name, offset)

    # ── 广播线程 ──
    broadcast.start()

    # ── 高温保护（后端常驻，无需自启动）──
    hot_protect.start()

    info(f"{len(_BASE_COLLECTORS)} 个采集线程 + 1 个广播线程已启动")


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
