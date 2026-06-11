#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""电池采集：电量 + 温度 + 高温保护"""
import re, time
from logger import info
from config import ADB_ADDRESS
from .base import cmd, _try_local


def collect(_bt_start: list) -> dict:
    """采集电池电量和温度，超 50°C 半小时自动杀 AP"""
    raw_output = _try_local("dumpsys battery 2>/dev/null", "dumpsys battery 2>/dev/null", 8)
    level_match = re.search(r"level:\s*(\d+)", raw_output)
    temp_match = re.search(r"temperature:\s*(\d+)", raw_output)
    temp_str = ""
    if temp_match:
        temp_str = f"{int(temp_match.group(1)) / 10:.1f}°C"
    # 电池高温保护
    temp_celsius = 0.0
    if temp_str.endswith("°C"):
        try:
            temp_celsius = float(temp_str[:-2])
        except (ValueError, TypeError):
            pass
    if temp_celsius >= 50:
        if _bt_start[0] is None:
            _bt_start[0] = time.time()
            info(f"电池 {temp_str} 超 50°C，开始计时")
        elif time.time() - _bt_start[0] >= 1800:
            info(f"电池 {temp_str} 超 50°C 已达 30 分钟，执行保护")
            cmd(f'adb -s {ADB_ADDRESS} shell "am force-stop com.bilibili.azurlane"', 5)
            cmd("proot-distro login ubuntu -- pkill -f 'python.*gui.py' 2>/dev/null || true", 5)
            cmd("pkill -f start_ap.sh 2>/dev/null || true", 3)
            info("已终止 AP 后端和碧蓝航线进程")
            _bt_start[0] = time.time()
    else:
        if _bt_start[0] is not None:
            info(f"电池温度恢复正常 {temp_str}，重置计时")
        _bt_start[0] = None
    return {"bt": level_match.group(1) + "%" if level_match else "?", "btt": temp_str}
