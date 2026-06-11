#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CPU 型号识别 + 核心频率采集"""
import re
from logger import info
from .base import _local, _try_local
from .shared import LOSTAT, _CPU_MAP, _mark_dirty


def collect_model() -> dict:
    """CPU 型号识别（60 秒），未知芯片/厂商自动学习"""
    result = {}
    result.update(LOSTAT)
    cpu_raw = LOSTAT.get("cpu_raw", "?")
    cpu_impl = LOSTAT.get("cpu_impl", "")
    core_count = LOSTAT.get("cc", "?")
    vendor_name = _CPU_MAP["implementers"].get(cpu_impl, "")
    if not vendor_name:
        for keyword, name in _CPU_MAP["vendor_keywords"].items():
            if keyword in cpu_raw.lower():
                vendor_name = name
                break
    chip_id = cpu_raw.lower().replace(" ", "")
    chip_match = re.search(r'(SM\d+|SDM\d+|MSM\d+|MT\d+|Kirin\w*|Exynos\w*)', cpu_raw, re.I)
    if chip_match:
        chip_id = chip_match.group(1).lower().replace(" ", "")
    chip_name = _CPU_MAP["chips"].get(chip_id)
    # 尝试匹配 cpu_raw 中的每个单词（如 "KONA" → "kona"）
    if not chip_name:
        for word in cpu_raw.split():
            w = word.lower().strip(",:;.()")
            if w and len(w) >= 2:
                chip_name = _CPU_MAP["chips"].get(w)
                if chip_name:
                    chip_id = w
                    break
    if not chip_name and len(chip_id) > 6:
        chip_name = _CPU_MAP["chips"].get(chip_id[:6])
    if not chip_name and len(chip_id) > 5:
        chip_name = _CPU_MAP["chips"].get(chip_id[:5])
    # 自动学习
    if not chip_name and chip_id and chip_id != "?" and len(chip_id) >= 3:
        new_chip_name = cpu_raw.upper() if len(cpu_raw) > 2 and cpu_raw != "?" else chip_id.upper()
        _CPU_MAP["chips"][chip_id] = new_chip_name
        chip_name = new_chip_name
        info(f"芯片已自动学习: {chip_id} → {new_chip_name}")
        _mark_dirty()
    if not vendor_name and cpu_impl and cpu_impl != "?" and len(cpu_impl) >= 2:
        _CPU_MAP["implementers"][cpu_impl] = f"厂商({cpu_impl})"
        vendor_name = _CPU_MAP["implementers"][cpu_impl]
        info(f"厂商已自动学习: {cpu_impl}")
        _mark_dirty()
    display_parts = []
    if vendor_name:
        display_parts.append(vendor_name)
    if chip_name:
        display_parts.append(chip_name)
    elif cpu_raw and cpu_raw != "?":
        display_parts.append(cpu_raw.upper())
    if core_count and core_count != "?":
        display_parts.append(f"· {core_count}核")
    result["cpu_model"] = " ".join(display_parts) if display_parts else "?"
    return result


def collect_freq() -> dict:
    """读取各 CPU 核心当前频率（本地 sysfs 优先，失败回退 ADB）"""
    _CMD = ("for i in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do "
            "cat \"/sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq\" 2>/dev/null || break; done")
    raw_output = _try_local(_CMD, _CMD, 2)
    freqs = [int(x) for x in raw_output.strip().split() if x.strip().isdigit()]
    if not freqs:
        return {"cf_small": 0, "cf_big": 0}
    core_count = len(freqs)
    mid_index = core_count // 2
    small_cores = freqs[:mid_index]
    big_cores = freqs[mid_index:]
    freq_small = round(sum(small_cores) / len(small_cores) / 1000, 1) if small_cores else 0
    freq_big = round(sum(big_cores) / len(big_cores) / 1000, 1) if big_cores else 0
    return {"cf_small": freq_small, "cf_big": freq_big}
