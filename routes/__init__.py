#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路由包 — 注册所有 Flask 路由"""

from . import misc, config_routes


def register_all(app) -> None:
    """在 Flask app 上注册所有路由"""
    misc.register(app)
    config_routes.register(app)
