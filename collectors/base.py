#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集器基础工具模块
提供 shell 执行、速率格式化、线程启动等通用函数。
"""
import subprocess, time, threading
from logger import error
from config import ADB_ADDRESS
from .shared import _data_lock, _sd


def cmd(c: str, to: int = 8) -> str:
    """执行 shell 命令并返回 stdout"""
    try:
        return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=to).stdout.strip()
    except Exception:
        return ""


def _fb(x: float) -> str:
    """格式化字节速率（B/s → KB/s → MB/s）"""
    for u, s in [(1048576, "MB/s"), (1024, "KB/s")]:
        if x >= u:
            return f"{x / u:.1f}{s}"
    return f"{x:.0f}B/s"


def _local(c: str, to: int = 5) -> str:
    """本地 shell 执行（Termux 直接运行，无需 ADB）"""
    return cmd(c, to)


def _adb(c: str, to: int = 5) -> str:
    """通过 ADB 在设备上执行"""
    return cmd(f'adb -s {ADB_ADDRESS} shell "{c}"', to)


def _try_local(c_local: str, c_adb: str, to: int = 5) -> str:
    """先尝试本地执行，失败则回退到 ADB"""
    r = _local(c_local, to)
    if r:
        return r
    return _adb(c_adb, to)


def _start_thread(interval: float, fn, name: str = "", offset: float = 0) -> threading.Thread:
    """启动一个独立采集线程，每 interval 秒运行一次 fn，offset 为首次启动延迟(秒)"""
    def loop():
        if offset > 0:
            time.sleep(offset)
        while True:
            try:
                t0 = time.time()
                data = fn()
                if data:
                    with _data_lock:
                        _sd.update(data)
                elapsed = time.time() - t0
                remaining = interval - elapsed
                if remaining > 0:
                    time.sleep(remaining)
            except Exception as e:
                error(f"[{name}] {e}")
                time.sleep(1)
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t
