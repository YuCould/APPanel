#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AP 存活检测 + IP 地址 + 运行时间"""
import re, socket
from config import AP_HOST, AP_PORT
from .base import cmd
from .shared import _ap_ever_online


def collect() -> dict:
    """检测 AP 后端是否在线、获取 IP 和运行时间"""
    result = {}
    ap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ap_socket.settimeout(1)
    global _ap_ever_online
    try:
        ap_socket.connect((AP_HOST, AP_PORT))
        result["ap_online"] = True
        _ap_ever_online = True
    except OSError:
        result["ap_online"] = False
    finally:
        ap_socket.close()
    result["ap_available"] = _ap_ever_online
    result["ip"] = cmd(r"netstat -ie 2>/dev/null|grep -A1 wlan0|grep -oE 'inet [0-9.]+|inet6 [0-9a-f:]+'|awk '{print $2}'|head -3", 3) or "?"
    result["ip6"] = cmd(r"netstat -ie 2>/dev/null|grep -A1 wlan0|grep -oE 'inet6 [0-9a-f:]+'|awk '{print $2}'|head -2", 3) or ""
    uptime_raw = cmd("uptime -p", 3) or "?"
    uptime_raw = uptime_raw.replace(",", "")
    uptime_match = re.search(r"up\s*(?:(\d+)\s+weeks?\s*)?(?:(\d+)\s+days?\s*)?(?:(\d+)\s+hours?\s*)?(?:(\d+)\s+minutes?\s*)?(?:(\d+)\s+seconds?\s*)?", uptime_raw)
    result["up"] = (
        (uptime_match.group(1) or "0") + "周-" + (uptime_match.group(2) or "0") + "天:"
        + (uptime_match.group(3) or "0") + "时:" + (uptime_match.group(4) or "0") + "分:"
        + (uptime_match.group(5) or "0") + "秒"
    ) if uptime_match else "?"
    return result
