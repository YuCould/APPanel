#!/data/data/com.termux/files/usr/bin/bash
echo "=== 启动 AP 后端 ==="
kill $(cat ~/ap_backend.pid 2>/dev/null) 2>/dev/null
nohup proot-distro login ubuntu -- bash -c 'export PATH=$PATH:/root/.local/bin && cd /root/AzurPilot && uv run python gui.py' > ~/ap_backend.log 2>&1 &
echo $! > ~/ap_backend.pid
echo "PID: $(cat ~/ap_backend.pid)"
echo "日志: ~/ap_backend.log"
