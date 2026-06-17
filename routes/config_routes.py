#!/us,/,in,env ,ytho,3.,,,,...,,
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
        "start": "[ -f ~/APPanel/start_ap.sh ] && bash ~/APPanel/start_ap.sh >/dev/null 2>&1",
    },
    "hot_protect": {
        "label": "电池≥50°C持续15分钟杀进程（后端控制）",
        "check": "pgrep -f dashboard.py > /dev/null",
        "start": ":",
    },
    "fix_adb_port": {
        "label": "自动固定ADB端口为5555",
        "check": "pgrep -f fix_adb_watch > /dev/null",
        "start": "nohup sh -c '#fix_adb_watch\nwhile sleep 60; do\n  if ! adb get-state 2>/dev/null | grep -q device; then\n    port=$(dumpsys adb 2>/dev/null | grep -o \"port=[0-9]*\" | head -1 | cut -d= -f2)\n    if [ -z \"$port\" ] || [ \"$port\" = \"null\" ]; then\n      port=$(settings get global adb_wifi_connection_port 2>/dev/null)\n    fi\n    if [ -n \"$port\" ] && [ \"$port\" != \"null\" ]; then\n      adb connect 127.0.0.1:\"$port\" 2>/dev/null\n      sleep 4\n      adb tcpip 5555 2>/dev/null\n      sleep 2\n      adb connect 127.0.0.1:5555 2>/dev/null\n    fi\n  fi\ndone' > /dev/null 2>&1 &",
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
    """将 autostart 配置写入 ~/.bashrc 和 ~/.bash_profile"""
    msgs = []
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        content = _generate_bashrc(autostart)
        with open(bashrc_path, "w") as f:
            f.write(content)
        enabled = sum(1 for v in autostart.values() if v)
        msgs.append(f"已更新 .bashrc（{enabled} 项自启动）")
    except Exception as e:
        msgs.append(f".bashrc 写入失败: {e}")
    # 确保 .bash_profile 会 source .bashrc（Termux 登录 shell 需要）
    try:
        bp = os.path.expanduser("~/.bash_profile")
        src_line = "source ~/.bashrc"
        if os.path.exists(bp):
            with open(bp) as f:
                if src_line in f.read():
                    return "；".join(msgs)
        with open(bp, "a") as f:
            f.write(f"\n{src_line}\n")
        msgs.append("已修复 .bash_profile 加载")
    except Exception as e:
        msgs.append(f".bash_profile 写入失败: {e}")
    return "；".join(msgs)


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
                # 处理自启动（仅配置变更时才写入 .bashrc）
                autostart = _m.get("autostart", {})
                old_autostart = _CPU_MAP.get("autostart", {})
                _CPU_MAP["autostart"] = autostart
                bashrc_msg = ""
                if autostart != old_autostart:
                    bashrc_msg = _apply_autostart(autostart)
                # 处理隐藏进程
                hp = _m.get("hidden_procs")
                if hp is not None and isinstance(hp, dict):
                    _CPU_MAP["hidden_procs"] = hp
                # 处理采集速度（每个通道独立设置）
                cs = _m.get("collect_speeds")
                if cs is not None and isinstance(cs, dict):
                    _CPU_MAP["collect_speeds"] = {
                        k: max(0.1, float(v)) for k, v in cs.items()
                        if k in ("fast", "medium", "slow")
                    }
                # 广播新的包名映射给所有 WS 客户端
                try:
                    from collectors.ws import WS_CLIENTS, ws_broadcast
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(ws_broadcast({
                        "_pkg_map": _CPU_MAP.get("packages", {}),
                    }))
                    loop.close()
                except Exception:
                    pass
                msg = "已保存"
                if bashrc_msg:
                    msg += f"，{bashrc_msg}"
                return jsonify({"status": "ok", "message": msg})
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
