#!/us,/bi,/env,pytho,3
# -*- coding: utf-8 -*-
"""
持久 ADB / Local Shell 模块（多通道）

每个命名通道拥有独立的 ADB shell 和本地 shell 进程，互不干扰。
内置通道: fast, medium, slow, action
"""
import subprocess, threading, time, uuid
from logger import info, error, warn

_ADB_ADDR = "127.0.0.1:5555"
_CMD_TIMEOUT = 15          # 单条命令超时(秒)
_CHANNELS = ["fast", "freq", "mem", "proc", "medium", "slow", "ap", "action"]

# 每个通道独立存储: {name: {"adb": Popen, "local": Popen, "adb_lock": Lock, "local_lock": Lock}}
_channels = {}


def _make_tag() -> str:
    return f"__END_{uuid.uuid4().hex[:8]}__"


def _start_adb(name: str) -> None:
    """启动指定通道的持久 ADB shell 进程"""
    try:
        proc = subprocess.Popen(
            ["adb", "-s", _ADB_ADDR, "shell"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        _channels[name]["adb"] = proc
        info(f"[{name}] ADB shell 已启动 (PID={proc.pid})")
    except Exception as e:
        error(f"[{name}] ADB shell 启动失败: {e}")
        _channels[name]["adb"] = None


def _start_local(name: str) -> None:
    """启动指定通道的持久本地 shell 进程（Termux bash）"""
    try:
        proc = subprocess.Popen(
            ["bash", "--norc"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        _channels[name]["local"] = proc
        info(f"[{name}] 本地 shell 已启动 (PID={proc.pid})")
    except Exception as e:
        error(f"[{name}] 本地 shell 启动失败: {e}")
        _channels[name]["local"] = None


def _exec(proc, lock, cmd: str, timeout: int, name: str) -> str:
    """在指定通道的持久 shell 中执行一条命令，返回 stdout"""
    if proc is None or proc.poll() is not None:
        return ""
    tag = _make_tag()
    full_cmd = f"{cmd}\necho {tag}\n"
    with lock:
        try:
            proc.stdin.write(full_cmd.encode())
            proc.stdin.flush()
        except Exception as e:
            error(f"[{name}] 写入失败: {e}")
            return ""
        out_lines = []
        deadline = time.time() + (timeout or _CMD_TIMEOUT)
        try:
            while time.time() < deadline:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.decode(errors="replace").rstrip("\r\n")
                if line == tag:
                    return "\n".join(out_lines)
                out_lines.append(line)
        except Exception as e:
            error(f"[{name}] 读取失败: {e}")
            return ""
        warn(f"[{name}] 命令超时 ({timeout}s): {cmd[:60]}")
        return "\n".join(out_lines)


# ── 公开 API ──

def start() -> None:
    """启动所有通道的持久 shell"""
    for name in _CHANNELS:
        _channels[name] = {"adb": None, "local": None,
                           "adb_lock": threading.Lock(), "local_lock": threading.Lock()}
        _start_adb(name)
        _start_local(name)
    info(f"已启动 {len(_CHANNELS)} 个通道: {_CHANNELS}")


def stop() -> None:
    """停止所有通道的持久 shell"""
    for name, ch in _channels.items():
        for key, label in [("adb", "ADB"), ("local", "Local")]:
            proc = ch.get(key)
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(3)
                except Exception:
                    proc.kill()
                info(f"[{name}] {label} shell 已停止")


def _ensure_channel(name: str) -> dict:
    """获取/创建通道，自动初始化"""
    if name not in _channels:
        _channels[name] = {"adb": None, "local": None,
                           "adb_lock": threading.Lock(), "local_lock": threading.Lock()}
        _start_adb(name)
        _start_local(name)
    return _channels[name]


def _adb_channel(proc_key: str, lock_key: str,
                 start_fn, cmd: str, timeout: int, name: str) -> str:
    """通用通道执行包装"""
    ch = _ensure_channel(name)
    proc = ch[proc_key]
    lock = ch[lock_key]
    if proc is None or proc.poll() is not None:
        warn(f"[{name}] 断开 [{proc_key}]，尝试重连...")
        start_fn(name)
        proc = ch[proc_key]
        if proc is None or proc.poll() is not None:
            return ""
    return _exec(proc, lock, cmd, timeout, name)


def adb(cmd: str, timeout: int = 10, channel: str = "fast") -> str:
    """在指定通道的持久 ADB shell 中执行命令"""
    return _adb_channel("adb", "adb_lock", _start_adb, cmd, timeout, channel)


def local(cmd: str, timeout: int = 5, channel: str = "fast") -> str:
    """在指定通道的持久本地 shell 中执行命令"""
    return _adb_channel("local", "local_lock", _start_local, cmd, timeout, channel)


def adb_fast(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="fast")
def local_fast(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="fast")

def adb_freq(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="freq")
def local_freq(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="freq")

def adb_mem(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="mem")
def local_mem(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="mem")

def adb_proc(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="proc")
def local_proc(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="proc")

def adb_medium(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="medium")
def local_medium(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="medium")

def adb_slow(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="slow")
def local_slow(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="slow")

def adb_ap(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="ap")
def local_ap(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="ap")

def adb_action(cmd: str, timeout: int = 10) -> str:
    return adb(cmd, timeout, channel="action")
def local_action(cmd: str, timeout: int = 5) -> str:
    return local(cmd, timeout, channel="action")


def get_channel_adb_pids() -> dict:
    """返回 {通道名: ADB shell PID} 映射，供前端标记采集通道"""
    result = {}
    for name, ch in _channels.items():
        proc = ch.get("adb")
        if proc and proc.poll() is None:
            result[name] = proc.pid
    return result


def get_channel_local_pids() -> dict:
    """返回 {通道名: 本地 bash PID} 映射，供前端标记本地 shell 通道"""
    result = {}
    for name, ch in _channels.items():
        proc = ch.get("local")
        if proc and proc.poll() is None:
            result[name] = proc.pid
    return result
