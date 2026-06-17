#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集器基础工具模块
提供持久 shell 执行、线程启动等通用函数。
"""
import subprocess, time, threading
from logger import error
from .adb_shell import (
    adb as _adb_persist, local as _local_persist,
    adb_action as _adb_action_persist, local_action as _local_action_persist,
    adb_fast as _adb_fast_persist, local_fast as _local_fast_persist,
    adb_freq as _adb_freq_persist, local_freq as _local_freq_persist,
    adb_mem as _adb_mem_persist, local_mem as _local_mem_persist,
    adb_proc as _adb_proc_persist, local_proc as _local_proc_persist,
    adb_medium as _adb_medium_persist, local_medium as _local_medium_persist,
    adb_slow as _adb_slow_persist, local_slow as _local_slow_persist,
    adb_ap as _adb_ap_persist, local_ap as _local_ap_persist,
)
from .shared import _data_lock, _sd, _sd_event


def cmd(c: str, to: int = 8) -> str:
    """执行本地 shell 命令（回退到 subprocess，仅用于少量场景）"""
    try:
        return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=to).stdout.strip()
    except Exception:
        return ""


def _local(c: str, to: int = 5) -> str:
    """使用持久本地 shell 执行"""
    return _local_persist(c, to)


def _adb(c: str, to: int = 10) -> str:
    """使用持久 ADB shell 执行"""
    return _adb_persist(c, to)


def _adb_fast(c: str, to: int = 10) -> str:
    return _adb_fast_persist(c, to)
def _local_fast(c: str, to: int = 5) -> str:
    return _local_fast_persist(c, to)

def _adb_freq(c: str, to: int = 10) -> str:
    return _adb_freq_persist(c, to)
def _local_freq(c: str, to: int = 5) -> str:
    return _local_freq_persist(c, to)

def _adb_mem(c: str, to: int = 10) -> str:
    return _adb_mem_persist(c, to)
def _local_mem(c: str, to: int = 5) -> str:
    return _local_mem_persist(c, to)

def _adb_proc(c: str, to: int = 10) -> str:
    return _adb_proc_persist(c, to)
def _local_proc(c: str, to: int = 5) -> str:
    return _local_proc_persist(c, to)

def _adb_medium(c: str, to: int = 10) -> str:
    return _adb_medium_persist(c, to)
def _local_medium(c: str, to: int = 5) -> str:
    return _local_medium_persist(c, to)

def _adb_slow(c: str, to: int = 10) -> str:
    return _adb_slow_persist(c, to)
def _local_slow(c: str, to: int = 5) -> str:
    return _local_slow_persist(c, to)

def _adb_ap(c: str, to: int = 10) -> str:
    return _adb_ap_persist(c, to)
def _local_ap(c: str, to: int = 5) -> str:
    return _local_ap_persist(c, to)

def _adb_action(c: str, to: int = 10) -> str:
    """使用 action 通道的持久 ADB shell 执行（不阻塞采集）"""
    return _adb_action_persist(c, to)

def _local_action(c: str, to: int = 5) -> str:
    """使用 action 通道的持久本地 shell 执行（不阻塞采集）"""
    return _local_action_persist(c, to)


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
                        _sd_event.set()
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
