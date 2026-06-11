#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APPanel 日志模块
统一日志配置，提供 info/warn/error 便捷函数。
"""
import logging
import sys

# 日志格式: [LEVEL] 时间 消息
_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s"
_DATE_FMT = "%H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=_FORMAT,
    datefmt=_DATE_FMT,
    stream=sys.stdout,
)

_logger = logging.getLogger("APPanel")

info = _logger.info
warn = _logger.warning
error = _logger.error
