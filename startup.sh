#!/usr/bin/env b?sh
# ============================================
# APPanel 自启动脚本
# Termux 开机/手动执行: bash startup.sh
# ============================================
APPANEL_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── SSH 服务 ──
if ! pgrep -x sshd > /dev/null; then
    echo "[startup] 启动 sshd..."
    sshd
else
    echo "[startup] sshd 已在运行"
fi

# ── APPanel 仪表盘 ──
if ! pgrep -f 'python3.*dashboard.py' > /dev/null; then
    echo "[startup] 启动 APPanel 仪表盘..."
    cd "$APPANEL_DIR" && nohup python3 dashboard.py > ~/dashboard_new.log 2>&1 &
    echo "[startup] APPanel 已启动 (PID=$!)"
fi

# ── AP 后端（proot-distro ubuntu 内）──
if [ -f "$APPANEL_DIR/start_ap.sh" ]; then
    echo "[startup] 启动 AP 后端（proot-distro ubuntu）..."
    bash "$APPANEL_DIR/start_ap.sh" > /dev/null 2>&1 &
    echo "[startup] AP 后端启动命令已发送（等待 60s 后生效）"
else
    echo "[startup] APPanel 已在运行"
fi
