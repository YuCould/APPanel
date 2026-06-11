#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设置 API：读取/保存 settings.json，自动生成 .bashrc"""
import json, os
from flask import jsonify, request
from collectors.shared import _CPU_MAP, _CPU_MAP_PATH

# 自启动项定义: key → {label, check_cmd, start_cmd}
_AUTOSTART_ITEMS = {
    "sshd": {
        "label": "SSH 服务",
        "check": "pgrep -x sshd > /dev/null",
        "start": "sshd",
    },
    "dashboard": {
        "label": "APPanel 仪表盘",
        "check": "pgrep -f 'python3.*dashboard.py' > /dev/null",
        "start": "cd ~/APPanel && nohup python3 dashboard.py > ~/dashboard_new.log 2>&1 &",
    },
    "ap_backend": {
        "label": "AP 后端",
        "check": "pgrep -f 'python.*gui.py' > /dev/null",
        "start": "[ -f ~/start_ap.sh ] && bash ~/start_ap.sh >/dev/null 2>&1",
    },
}


def _generate_bashrc(autostart: dict) -> str:
    """根据 autostart 配置生成 .bashrc 内容"""
    lines = ["# 自启动 - 由 APPanel 设置管理，修改请通过页面设置"]
    for key, cfg in _AUTOSTART_ITEMS.items():
        if autostart.get(key, False):
            lines.append(f"if ! {cfg['check']}; then")
            lines.append(f"    {cfg['start']}")
            lines.append("fi")
    lines.append("")
    return "\n".join(lines)


def _apply_autostart(autostart: dict) -> str:
    """将 autostart 配置写入 ~/.bashrc"""
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        content = _generate_bashrc(autostart)
        with open(bashrc_path, "w") as f:
            f.write(content)
        enabled = sum(1 for v in autostart.values() if v)
        return f"已更新 .bashrc（{enabled} 项自启动）"
    except Exception as e:
        return f".bashrc 写入失败: {e}"


def register(app) -> None:
    @app.route("/api/config", methods=["GET", "POST"])
    def api_config():
        if request.method == "POST":
            try:
                data = request.get_json(force=True)
                content = data.get("content", "")
                json.loads(content)  # 验证 JSON
                with open(_CPU_MAP_PATH, "w", encoding="utf-8") as f:
                    f.write(content)
                _m = json.loads(content)
                _CPU_MAP["chips"] = _m.get("chips", {})
                _CPU_MAP["packages"] = _m.get("packages", {})
                _CPU_MAP["implementers"] = _m.get("implementers", {})
                _CPU_MAP["vendor_keywords"] = _m.get("vendor_keywords", {})
                # 处理自启动
                autostart = _m.get("autostart", {})
                _CPU_MAP["autostart"] = autostart
                bashrc_msg = _apply_autostart(autostart)
                return jsonify({
                    "status": "ok",
                    "message": f"已保存，{bashrc_msg}",
                })
            except json.JSONDecodeError as e:
                return jsonify({"status": "error", "message": f"JSON 格式错误: {e}"}), 400
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        # GET
        try:
            with open(_CPU_MAP_PATH, encoding="utf-8") as f:
                content = f.read()
            return jsonify({"status": "ok", "content": content})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
