#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高温保护模块
监控电池温度，≥50°C 累计 15 分钟后通过 ADB 杀进程。
低于 50°C 重置计数器。
"""
import time, threading
from logger import info, error
from .shared import _sd, _CPU_MAP
from .base import _adb_action


# 计数器状态
_hot_counter = 0
_HOT_THRESHOLD = 500       # dumpsys battery temperature 十分位, 500 = 50.0°C
_HOT_LIMIT = 90            # 90 次 × 10s ≈ 15 分钟
_CHECK_INTERVAL = 10       # 检查间隔(秒)


def _kill_azurlane():
    """杀碧蓝航线"""
    r = _adb_action("am force-stop com.bilibili.azurlane", 5)
    info(f"[高温保护] 已杀碧蓝航线: {'ok' if not r else r}")


def _kill_ap_hot():
    """杀 AP 后端 + Ubuntu"""
    _adb_action("am force-stop com.bilibili.azurlane", 5)
    _adb_action("pkill -f proot-distro", 3)
    _adb_action("pkill -f ubuntu", 3)
    info("[高温保护] 已杀 AP 后端 + Ubuntu")


def start():
    """启动高温保护线程"""
    def _loop():
        global _hot_counter
        while True:
            try:
                time.sleep(_CHECK_INTERVAL)
                # 检查用户是否关闭了高温保护
                if not _CPU_MAP.get("autostart", {}).get("hot_protect", True):
                    _hot_counter = 0
                    continue
                bt_raw = _sd.get("bt_raw")
                btt_raw = _sd.get("btt_raw")
                # 优先用 btt_raw（电池温度），回退 bt_raw（电量）
                temp = btt_raw if btt_raw is not None else None
                if temp is None:
                    continue
                if temp >= _HOT_THRESHOLD:
                    _hot_counter += 1
                    info(f"[高温保护] 累计 {_hot_counter}/{_HOT_LIMIT} (temp={temp})")
                    if _hot_counter >= _HOT_LIMIT:
                        _kill_azurlane()
                        _kill_ap_hot()
                        _hot_counter = 0
                else:
                    if _hot_counter > 0:
                        info(f"[高温保护] 温度已下降 ({temp})，计数器重置")
                    _hot_counter = 0
            except Exception as e:
                error(f"[高温保护] {e}")
    threading.Thread(target=_loop, daemon=True).start()
    info(f"[高温保护] 已启动 (阈值={_HOT_THRESHOLD/10}°C, 累计{_HOT_LIMIT*_CHECK_INTERVAL}秒)")
