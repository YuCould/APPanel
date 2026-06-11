#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APPanel — Android 设备实时监控仪表盘
====================================
入口文件：启动采集器 → 启动 WebSocket → 启动 Flask。

模块结构：
  dashboard.py        入口（本文件）
  server.py           Flask + WebSocket 服务
  collectors/         数据采集器包
  routes/             Flask 路由包
  page.html           前端页面
  settings.json       芯片/应用映射配置
"""
import time, threading
from collectors import start_collectors
from server import start_ws, run

if __name__ == "__main__":
    start_collectors()
    time.sleep(2)
    threading.Thread(target=start_ws, daemon=True).start()
    time.sleep(1)
    run()
