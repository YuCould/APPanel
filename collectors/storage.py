#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""存储采集（从 df 本地读取）"""
from .base import cmd


def collect() -> dict:
    """读取 /data 分区存储占用 + APPanel 项目目录大小"""
    sr = cmd("df -h /data|tail -1", 2).split()
    result = {}
    if len(sr) >= 5:
        result.update({"st": sr[1], "su": sr[2], "sa": sr[3], "sp": int(sr[4].replace("%", ""))})
    else:
        result.update({"st": "?", "su": "?", "sa": "?", "sp": 0})
    # APPanel 项目目录大小
    project_size = cmd("du -sh ~/APPanel 2>/dev/null | cut -f1", 3)
    result["project_size"] = project_size if project_size else "?"
    return result
