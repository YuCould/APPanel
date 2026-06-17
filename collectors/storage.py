#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""存储采集（原始 stat 数据，dp 每 5 分钟更新一次）"""
from .base import _local_slow

_DU_COUNTER = 0        # du 调用计数器（每6次=5分钟更新一次）


def collect() -> dict:
    """读取 /data 分区原始字节 + APPanel 项目目录大小（降频）"""
    global _DU_COUNTER
    result = {}

    # ── 分区信息（df 兼容性最好）──
    sr = _local_slow("df /data 2>/dev/null|tail -1", 2).split()
    if len(sr) >= 5:
        # 1K-blocks, Used, Available, Use%
        result["sto_total_kb"] = int(sr[1]) if sr[1].isdigit() else 0
        result["sto_used_kb"] = int(sr[2]) if sr[2].isdigit() else 0
        result["sto_avail_kb"] = int(sr[3]) if sr[3].isdigit() else 0

    # ── 项目目录大小（每 6 次 = 约 5 分钟刷新一次，避免 du 遍历开销）──
    _DU_COUNTER += 1
    if _DU_COUNTER >= 6:
        _DU_COUNTER = 0
        ps = _local_slow("du -sb ~/APPanel 2>/dev/null | cut -f1", 3)
        if ps and ps.strip().isdigit():
            result["project_bytes"] = int(ps.strip())
    return result
