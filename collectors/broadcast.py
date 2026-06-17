#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广播线程模块
定期将采集数据从 _sd 同步到 CACHE 并通过 WebSocket 推送。
优化：仅推送变化的数据（diff），每 10 次做一次全量推送保证可靠性。
"""
import asyncio, threading, time
from .shared import _sd, _data_lock, _CPU_MAP
from .ws import CACHE, ws_broadcast

# 上一次推送的快照，用于计算 diff
_prev_snapshot: dict = {}
_full_counter = 0
_FULL_INTERVAL = 10  # 每 10 次循环做一次全量推送


def start() -> None:
    """广播循环: 每 0.5s 推送一次，仅推送变化的数据"""

    def _loop():
        global _prev_snapshot, _full_counter
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            try:
                time.sleep(0.5)
                # ── 从 _sd 同步到 CACHE ──
                with _data_lock:
                    if _sd:
                        CACHE.clear()
                        CACHE.update(_sd)
                # 每次广播附带持久字段
                CACHE["_pkg_map"] = _CPU_MAP.get("packages", {})
                CACHE["_hidden_procs"] = _CPU_MAP.get("hidden_procs", {})
                try:
                    from .adb_shell import get_channel_adb_pids, get_channel_local_pids
                    CACHE["_adb_pids"] = get_channel_adb_pids()
                    CACHE["_local_pids"] = get_channel_local_pids()
                except Exception:
                    pass

                if not CACHE:
                    continue

                # ── 计算 diff ──
                _full_counter += 1
                do_full = _full_counter >= _FULL_INTERVAL
                diff = {}
                for k, v in CACHE.items():
                    if k not in _prev_snapshot or _prev_snapshot[k] != v:
                        diff[k] = v
                # 检查已移除的键
                for k in _prev_snapshot:
                    if k not in CACHE:
                        diff[k] = None  # 通知前端清除

                if do_full or len(diff) > len(CACHE) // 2:
                    # 全量推送（数据变化太多时 diff 反而更贵）
                    loop.run_until_complete(ws_broadcast(CACHE))
                    _prev_snapshot = dict(CACHE)
                    _full_counter = 0
                elif diff:
                    loop.run_until_complete(ws_broadcast(diff))
                    # 更新快照
                    for k, v in diff.items():
                        if v is None:
                            _prev_snapshot.pop(k, None)
                        else:
                            _prev_snapshot[k] = v
            except Exception:
                pass

    threading.Thread(target=_loop, daemon=True).start()
