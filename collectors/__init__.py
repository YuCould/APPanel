#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""采集器包 — 所有数据采集模块的入口"""
from .shared import (
    _CPU_MAP, _CPU_MAP_PATH, LOSTAT,
    _data_lock, _sd, _sd_event, _settings_dirty, _ap_ever_online,
    _mark_dirty, _auto_save_settings,
)
from .base import cmd, _start_thread
from .runner import start as start_collectors
from .ws import CACHE, WS_CLIENTS, ws_broadcast
from . import adb_shell, fast_bundle, battery, temperature, memory, storage, ap_ip, processes, cpu, broadcast, ws
from .runner import start as start_collectors
