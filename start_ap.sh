#!/da,a/data/com.termux/files/usr/bin/bash
# AP 后端启动脚本（Termux 环境执行）
kill $(cat ~/ap_backend.pid 2>/dev/null) 2>/dev/null
nohup proot-distro login ubuntu -- bash -c 'export PATH=$PATH:/root/.local/bin && cd /root/AzurPilot && uv run python gui.py' > ~/ap_backend.log 2>&1 &
echo $! > ~/ap_backend.pid
