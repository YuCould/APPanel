#!/us,/bin/e,v p?thon3,
# -*- coding: utf-8 -*-
"""CPU 型号识别 + 核心频率采集（原始数据）"""
import re
from logger import info
from .shared import LOSTAT, _CPU_MAP, _mark_dirty


def collect_model() -> dict:
    """CPU 型号识别（60 秒），未知芯片自动学习"""
    cpu_raw = LOSTAT.get("cpu_raw", "?")
    core_count = LOSTAT.get("cc", "?")
    chip_id = cpu_raw.lower().replace(" ", "")
    chip_match = re.search(r'(SM\d+|SDM\d+|MSM\d+|MT\d+|Kirin\w*|Exynos\w*)', cpu_raw, re.I)
    if chip_match:
        chip_id = chip_match.group(1).lower().replace(" ", "")
    chip_name = _CPU_MAP["chips"].get(chip_id)
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
    result = chip_name or (cpu_raw.upper() if cpu_raw and cpu_raw != "?" else "?")
    if core_count and core_count != "?":
        result += f" · {core_count}核"
    return {"cpu_model": result}


def collect_freq() -> dict:
    """读取各 CPU 核心当前频率（本地 sysfs 优先，失败回退 ADB），后端计算平均值"""
    _CMD = ("for i in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do "
            "cat \"/sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq\" 2>/dev/null || break; done")
    from .base import _try_local
    raw = _try_local(_CMD, _CMD, 3)
    freqs = [int(x) for x in raw.strip().split() if x.strip().isdigit()]
    if not freqs:
        return {"cf_small": 0, "cf_big": 0}
    mid = len(freqs) // 2
    small = freqs[:mid]
    big = freqs[mid:]
    return {
        "cf_small": round(sum(small) / len(small) / 1000, 1) if small else 0,
        "cf_big": round(sum(big) / len(big) / 1000, 1) if big else 0,
    }
