#!/usr/,,n/en, python3//,/.,,/.,.//.///
# -*- coding: utf-8 -*-
"""中速采集：电池 + 当前前台应用（medium 通道）"""
from .base import _adb_medium


def collect() -> dict:
    """采集电池原始数据 + 当前前台应用"""
    result = {}

    # ── 电池（优先 sysfs 直接读文件，零开销；回退 dumpsys）──
    for _p in ("battery", "bms", "fg"):
        cap = _adb_medium(f"cat /sys/class/power_supply/{_p}/capacity 2>/dev/null", 2)
        if cap and cap.strip().isdigit():
            result["bt_raw"] = int(cap.strip())
            tmp = _adb_medium(f"cat /sys/class/power_supply/{_p}/temp 2>/dev/null", 2)
            if tmp and tmp.strip().isdigit():
                result["btt_raw"] = int(tmp.strip())
            break
    else:
        # sysfs 不可用，回退 dumpsys battery
        raw = _adb_medium("dumpsys battery 2>/dev/null", 8)
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("level:"):
                result["bt_raw"] = int(line.split()[-1])
            elif line.startswith("temperature:"):
                result["btt_raw"] = int(line.split()[-1])

    # ── 前台应用（单条命令走 medium 通道）──
    fg_raw = _adb_medium("dumpsys window 2>/dev/null|grep mCurrentFocus|cut -d/ -f1|awk '{print $NF}'", 5)
    pkg_name = fg_raw.split()[-1] if fg_raw else "?"
    if pkg_name.startswith("Window{"):
        pkg_name = pkg_name.split()[-1] if len(pkg_name.split()) > 1 else "?"
    result["fg_pkg"] = pkg_name

    return result
