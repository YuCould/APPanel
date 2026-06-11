#!/data/data/com.termux/files/usr/bin/bash
PID=$(cat ~/ap_backend.pid 2>/dev/null)
if [ -n "$PID" ]; then
    kill $PID 2>/dev/null
    rm ~/ap_backend.pid
    echo "AP 后端已停止 (PID: $PID)"
else
    echo "AP 后端未在运行"
fi
