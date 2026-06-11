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
        def _do():
            time.sleep(1)
            os.execl(sys.executable, sys.executable, *sys.argv)
        threading.Thread(target=_do, daemon=False).start()
        return jsonify({"status": "restarting"})

    @app.route("/api/screen", methods=["GET", "POST"])
    def screen():
        """熄屏挂机：SurfaceControl.setDisplayPowerMode(物理屏token, mode)"""
        from collectors.base import _adb
        from collectors.shared import _sd, _data_lock
        from collectors.ws import CACHE
        if request.method == "POST":
            action = request.get_json(force=True).get("action", "")
            if action == "off":
                _adb("svc power stayon true", 3)
                # 优先使用 SurfaceControl，失败则 fallback 到 KEYCODE_SLEEP (不锁频)
                r = _adb("app_process -Djava.class.path=/data/local/tmp/escrcpy.dex /data/local/tmp com.apanel.ScreenEscrcpy 0", 10)
                if not r:
                    _adb("input keyevent 223", 3)
                with _data_lock:
                    _sd["screen_on"] = False
                CACHE["screen_on"] = False
                return jsonify({"status": "ok", "screen": "off"})
            elif action == "on":
                r = _adb("app_process -Djava.class.path=/data/local/tmp/escrcpy.dex /data/local/tmp com.apanel.ScreenEscrcpy 2", 10)
                if not r:
                    _adb("input keyevent 224", 3)
                with _data_lock:
                    _sd["screen_on"] = True
                CACHE["screen_on"] = True
                return jsonify({"status": "ok", "screen": "on"})
            return jsonify({"status": "error", "message": "unknown action"}), 400
        # GET
        with _data_lock:
            is_on = _sd.get("screen_on", True)
        return jsonify({"status": "ok", "screen": "on" if is_on else "off"})

    @app.route("/api/screen/view")
    def screen_view():
        """通过 atx-agent 截取屏幕（JPEG）"""
        import subprocess
        # atx-agent JPEG
        try:
            r = subprocess.run(["curl", "-s", "http://127.0.0.1:7912/screenshot"],
                capture_output=True, timeout=8)
            if r.returncode == 0 and len(r.stdout) > 1000:
                from flask import Response
                return Response(r.stdout, mimetype='image/jpeg')
        except Exception:
            pass
        # 回退 screencap PNG
        try:
            r = subprocess.run(["adb", "-s", "127.0.0.1:5555", "exec-out", "screencap", "-p"],
                capture_output=True, timeout=8)
            if r.returncode == 0 and len(r.stdout) > 1000:
                from flask import Response
                return Response(r.stdout, mimetype='image/png')
        except Exception:
            pass
        return "", 500

    @app.route("/api/kill", methods=["POST"])
    def api_kill():
        """通过 ADB kill 进程（PID 或包名）"""
        from collectors.base import _adb
        data = request.get_json(force=True)
        pid = data.get("pid", "")
        pkg = data.get("pkg", "")
        results = []
        if pkg:
            r = _adb(f"am force-stop {pkg}", 5)
            results.append(f"force-stop {pkg}: {'ok' if not r else r}")
        if pid and pid.isdigit():
            r = _adb(f"kill {pid}", 5)
            results.append(f"kill {pid}: {'ok' if not r else r}")
        if not results:
            return jsonify({"status": "error", "message": "no pid or pkg provided"}), 400
        return jsonify({"status": "ok", "results": results})

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
            r = _sp.run(["git", "pull"], capture_output=True, text=True, timeout=30, cwd=_BASE)
            if r.returncode != 0:
                return jsonify({"status": "error", "message": r.stderr.strip() or r.stdout.strip()}), 500
            # 重启
            def _do():
                time.sleep(2)
                os.execl(sys.executable, sys.executable, *sys.argv)
            threading.Thread(target=_do, daemon=False).start()
            return jsonify({"status": "ok", "message": "更新成功，正在重启…", "output": r.stdout.strip()})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/ports", methods=["GET", "POST"])
    def api_ports():
        """读取/写入端口配置"""
        import json as _json
        _port_path = os.path.join(_BASE, "port_config.json")
        if request.method == "POST":
            try:
                data = request.get_json(force=True)
                content = {"说明": "端口配置覆盖文件，留空或删掉此文件则使用 config.py 中的默认值"}
                for k in ("flask_port", "ws_port", "ap_port", "adb_port"):
                    v = data.get(k)
                    content[k] = v if (v is not None and str(v).strip()) else None
                with open(_port_path, "w", encoding="utf-8") as f:
                    _json.dump(content, f, indent=2, ensure_ascii=False)
                return jsonify({"status": "ok", "message": "端口配置已保存，重启 APPanel 后生效"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        # GET
        try:
            with open(_port_path, encoding="utf-8") as f:
                cfg = _json.load(f)
            return jsonify({
                "status": "ok",
                "current": {
                    "flask_port": cfg.get("flask_port"),
                    "ws_port": cfg.get("ws_port"),
                    "ap_port": cfg.get("ap_port"),
                    "adb_port": cfg.get("adb_port"),
                },
                "defaults": {
                    "flask_port": 80,
                    "ws_port": 5001,
                    "ap_port": 22267,
                    "adb_port": 5555,
                },
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/mpegts.js")
    def mpegts_js():
        return "", 204

    @app.route("/index.png")
    def index_png():
        return send_file(os.path.join(_BASE, "index.png"), mimetype="image/png")