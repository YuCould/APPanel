#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""存储采集（从 df 本地读取）"""
from .base import cmd


def collect() -> dict:
    """读取 /data 分区存储占用"""
    sr = cmd("df -h /data|tail -1", 2).split()
    if len(sr) >= 5:
        return {"st": sr[1], "su": sr[2], "sa": sr[3], "sp": int(sr[4].replace("%", ""))}
    return {"st": "?", "su": "?", "sa": "?", "sp": 0}
