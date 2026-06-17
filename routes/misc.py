#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""杂项路由：首页、favicon、API 全量数据、重启"""
import os, threading, time, sys

from flask import jsonify, send_file, request

from collectors.ws import CACHE


def register(app) -> None:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @app.route("/favicon.ico")
    def favicon():
        for name, mime in [("favicon.ico", "image/x-icon"), ("favicon.png", "image/png")]:
            p = os.path.join(_BASE, name)
            if os.path.exists(p):
                return send_file(p, mimetype=mime)
        return "", 204

    @app.route("/")
    def idx():
        try:
            with open(os.path.join(_BASE, "page.html")) as f:
                return f.read()
        except (OSError, IOError):
            return "Dashboard page not found"

    @app.route("/api/all")
    def api():
        return jsonify(CACHE)

    @app.route("/api/restart", methods=["POST"])
    def restart():
        import subprocess as _sp
        def _do():
            time.sleep(1)
            # 启动新进程，然后退出当前进程（比 os.execl 更可靠）
            _sp.Popen([sys.executable] + sys.argv,
                      stdin=_sp.DEVNULL, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
            os._exit(0)
        threading.Thread(target=_do, daemon=False).start()
        return jsonify({"status": "restarting"})

    @app.route("/api/kill", methods=["POST"])
    def api_kill():
        """通过 ADB kill 进程（PID 或包名，走 action 通道不阻塞采集）"""
        from collectors.base import _adb_action
        data = request.get_json(force=True)
        pid = data.get("pid", "")
        pkg = data.get("pkg", "")
        results = []
        if pkg:
            r = _adb_action(f"am force-stop {pkg}", 5)
            results.append(f"force-stop {pkg}: {'ok' if not r else r}")
        if pid and pid.isdigit():
            r = _adb_action(f"kill {pid}", 5)
            results.append(f"kill {pid}: {'ok' if not r else r}")
        if not results:
            return jsonify({"status": "error", "message": "no pid or pkg provided"}), 400
        return jsonify({"status": "ok", "results": results})

    @app.route("/api/kill-ubuntu", methods=["POST"])
    def api_kill_ubuntu():
        """强制终止 proot-distro ubuntu 所有进程"""
        import subprocess as _sp
        try:
            _sp.run("pkill -f 'proot-distro.*ubuntu' 2>/dev/null; pkill -f 'python.*gui.py' 2>/dev/null; pkill -f 'AzurPilot' 2>/dev/null",
                    shell=True, timeout=5)
            return jsonify({"status": "ok", "message": "已终止 proot-distro ubuntu 相关进程"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/version")
    def api_version():
        """获取本地 Git 版本和远程最新版本"""
        import subprocess as _sp
        local_hash = _sp.run(["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=_BASE).stdout.strip()
        local_time = _sp.run(["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, timeout=5, cwd=_BASE).stdout.strip()
        remote_hash = ""
        try:
            r = _sp.run(["git", "ls-remote", "origin", "HEAD"],
                capture_output=True, text=True, timeout=10, cwd=_BASE)
            if r.returncode == 0 and r.stdout.strip():
                remote_hash = r.stdout.strip().split()[0][:7]
        except Exception:
            pass
        return jsonify({
            "local": {"hash": local_hash, "time": local_time},
            "remote": {"hash": remote_hash},
        })

    @app.route("/api/update", methods=["POST"])
    def api_update():
        """一键拉取 Git 更新并重启"""
        import subprocess as _sp
        try:
            r = _sp.run(["git", "pull"],
                capture_output=True, text=True, timeout=30, cwd=_BASE)
            if r.returncode != 0:
                return jsonify({"status": "error", "message": r.stderr.strip() or r.stdout.strip()}), 500
            # 重启
            def _do():
                time.sleep(2)
                _sp.Popen([sys.executable] + sys.argv,
                          stdin=_sp.DEVNULL, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
                os._exit(0)
            threading.Thread(target=_do, daemon=False).start()
            return jsonify({"status": "ok", "message": "更新成功，正在重启…", "output": r.stdout.strip()})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/ports", methods=["GET", "POST"])
    def api_ports():
        """读取/写入端口配置（存入 settings.json）"""
        import json as _json
        _settings_path = os.path.join(_BASE, "settings.json")
        if request.method == "POST":
            try:
                # 读取当前 settings.json
                if os.path.exists(_settings_path):
                    with open(_settings_path, encoding="utf-8") as f:
                        cfg = _json.load(f)
                else:
                    cfg = {}
                # 写入端口字段
                for k in ("flask_port", "ws_port", "ap_port", "adb_port", "screen_port"):
                    v = request.get_json(force=True).get(k)
                    cfg[k] = v if (v is not None and str(v).strip()) else None
                with open(_settings_path, "w", encoding="utf-8") as f:
                    _json.dump(cfg, f, indent=2, ensure_ascii=False)
                return jsonify({"status": "ok", "message": "端口配置已保存，重启 APPanel 后生效"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        # GET
        _defaults = {"flask_port": 80, "ws_port": 5001, "ap_port": 22267, "adb_port": 5555, "screen_port": 20000}
        _current = {}
        try:
            if os.path.exists(_settings_path):
                with open(_settings_path, encoding="utf-8") as f:
                    cfg = _json.load(f)
                for k in _defaults:
                    _current[k] = cfg.get(k)
        except Exception:
            pass
        return jsonify({"status": "ok", "current": _current, "defaults": _defaults})

    @app.route("/index.png")
    def index_png():
        return send_file(os.path.join(_BASE, "index.png"), mimetype="image/png")