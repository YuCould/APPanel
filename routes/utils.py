#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路由工具函数：路径解析、文件保护检查"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASE_DIR = BASE_DIR  # 内部兼容
_EXTERNAL_DIRS: dict = {}
_PROTECTED_FILES: set = {
    "dashboard.py", "page.html", "settings.json", "favicon.ico",
    "favicon.png", ".gitignore", "requirements.txt", "README.md",
}

# 尝试查找 Downloads 路径
for _p in [
    os.path.expanduser("~/storage/downloads"),
    "/storage/emulated/0/Download",
    "/storage/emulated/0/download",
    "/sdcard/Download",
    "/sdcard/download",
]:
    if os.path.isdir(_p):
        _EXTERNAL_DIRS["downloads"] = _p
        break


def resolve_path(path: str) -> tuple:
    """解析路径，支持虚拟目录映射；返回 (绝对路径, 是否允许访问)"""
    if not path:
        return _BASE_DIR, True
    for vname, vpath in _EXTERNAL_DIRS.items():
        if path == vname or path.startswith(vname + "/"):
            sub = path[len(vname):].lstrip("/")
            abs_path = os.path.normpath(os.path.join(vpath, sub)) if sub else vpath
            return abs_path, True
    abs_path = os.path.normpath(os.path.join(_BASE_DIR, path))
    return abs_path, abs_path.startswith(_BASE_DIR)


def safe_path(path: str):
    """校验路径合法性，返回绝对路径或 None"""
    abs_path, ok = resolve_path(path)
    return abs_path if ok else None


def is_protected(abs_path: str) -> bool:
    """检查是否为受保护文件"""
    return os.path.basename(abs_path) in _PROTECTED_FILES


def is_external_dir(path: str) -> bool:
    """检查是否为外部虚拟目录"""
    return path in _EXTERNAL_DIRS


# ── API 响应辅助 ──

def ok_response(message: str = "", data: dict = None) -> dict:
    """构造成功响应"""
    resp = {"status": "ok"}
    if message:
        resp["message"] = message
    if data:
        resp.update(data)
    return resp


def error_response(message: str, status_code: int = 400) -> tuple:
    """构造错误响应（返回 Flask tuple）"""
    return {"status": "error", "message": message}, status_code
