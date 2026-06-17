#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AP 存活检测 + IP 地址 + 运行时间（ap 通道）"""
import re, socket
from config import AP_HOST, AP_PORT
from .base import _local_ap, _adb_ap
from .shared import _ap_ever_online


def _ip() -> dict:




def _ip() -> dict:
    """采集 IP 地址（从 getprop 读取，兼容所有环境）"""
    r = {"ip": "?", "ip6": ""}
    # 通过 ADB 读取 wlan0 地址（Android 原生命令，PATH 可靠）
    ni = _adb_ap("ip -f inet addr show wlan0 2>/dev/null", 3)
    m4 = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ni)
    if m4:
        r["ip"] = m4.group(1)
    # IPv6
    ni6 = _adb_ap("ip -f inet6 addr show wlan0 2>/dev/null", 3)
    m6 = re.search(r'inet6 ([\da-f:]+)', ni6)
    if m6:
        r["ip6"] = m6.group(1)
    return r


def _uptime() -> str:
    """采集系统运行时间"""
    raw = _local_ap("uptime -p 2>/dev/null", 3)
    if not raw or raw == "?":
        return "?"
    raw = raw.replace(",", "")
    m = re.search(r"up\s*(?:(\d+)\s+weeks?\s*)?(?:(\d+)\s+days?\s*)?(?:(\d+)\s+hours?\s*)?(?:(\d+)\s+minutes?\s*)?", raw)
    if m:
        w = m.group(1) or "0"
        d = m.group(2) or "0"
        h = m.group(3) or "0"
        mi = m.group(4) or "0"
        return f"{w}周-{d}天:{h}时:{mi}分"
    return raw or "?"





def _ap_process() -> dict:
    """查 AP 后端进程资源（Termux 宿主机直接可见，无需进 proot）"""
    r = {}
    try:
        ps_out = _local_ap("ps --no-headers -eo pid,%cpu,%mem,cmd 2>/dev/null | grep 'gui.py'", 3)
        for line in ps_out.split("\n"):
            line = line.strip()
            if not line or "grep" in line:
                continue
            parts = line.split()
            if len(parts) >= 4 and "gui.py" in parts[3]:
                r["ap_pid"] = int(parts[0])
                r["ap_cpu"] = parts[1]
                r["ap_mem"] = parts[2]
                break
    except Exception:
        pass
    return r


def collect() -> dict:
    """检测 AP 后端 + 屏幕服务 + IP + 运行时间 + AP 进程资源"""
    global _ap_ever_online
    result = {}

    # ── 屏幕服务检测（TCP 端口 20000）──
    try:
        sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sc.settimeout(1)
        sc.connect(("127.0.0.1", 20000))
        result["screen_online"] = True
        sc.close()
    except OSError:
        result["screen_online"] = False

    # ── AP 存活检测（TCP 端口）──
    ap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ap_socket.settimeout(1)
    try:
        ap_socket.connect((AP_HOST, AP_PORT))
        result["ap_online"] = True
        _ap_ever_online = True
    except OSError:
        result["ap_online"] = False
    finally:
        ap_socket.close()
    result["ap_available"] = _ap_ever_online

    # ── AP 进程资源（宿主机直接查）──
    if _ap_ever_online:
        result.update(_ap_process())

    # ── IP ──
    result.update(_ip())

    # ── 运行时间 ──
    result["up"] = _uptime()

    return result
