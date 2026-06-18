# APPanel — Android Device Real-Time Monitoring Dashboard

[GitHub](https://github.com/YuCould/APPanel) | [中文](README.md) | Runs in **Termux**, displays real-time Android device stats via **Web dashboard**. Features ADB wireless debugging, multi-channel persistent shells, diff-based WebSocket push — no root required.

### Key Features

- 🖥️ **Web Dashboard** — Flask + WebSocket real-time push, desktop/mobile responsive layout
- 📊 **Multi-Dimension Monitoring** — CPU usage, memory, storage, network speed/total, battery level/temp, process list
- 🔌 **ADB Wireless Debugging** — 8-channel persistent ADB shells, parallel collection without blocking
- ⚡ **Overheat Protection** — Battery ≥50°C for 15 minutes auto-kills AP backend and Azur Lane (⚠️ untested)
- 🔧 **Visual Settings** — Web-based editor for chip mapping, app name mapping, collection speed, hidden processes, autostart, ports
- 🔄 **Manual Update** — Version check, manual `git pull` with auto-restart
- 🛡️ **Autostart Daemon** — SSH/Dashboard/AP backend/Overheat kill/ADB port fix, toggle switches in settings
- 📱 **Process Management** — Sort, filter, KILL processes, dedicated kill page in settings

![APPanel Preview](index.png)

## Features

### Dashboard
- **CPU**: Real-time usage (all cores), animated gradient bar, active core count
- **Memory**: Used/total display with percentage bar
- **Storage**: Used/total display, auto GB/MB units, project directory size
- **Network**: Download/upload speed (1 decimal), Canvas 60fps Bezier chart (180 samples); IPv4 + IPv6 addresses, cumulative totals (default MB, auto-switch to GB above 1GB)
- **Battery**: Percentage with animated transition, temperature warning (>40°C alert, ≥50°C for 15 min kills AP and Azur Lane, ⚠️ untested)
- **CPU Temp**: Thermal zone reading, >70°C shows solder risk warning
- **Device Info**: Manufacturer + model (collected once)
- **Android Version**: API level
- **Uptime**: Computed client-side from server startup timestamp

### Process Management
- Real-time process list, default sorted by CPU descending, max 100 processes
- Sort by PID / CPU / Memory / App / Package name (ascending/descending)
- **Click any row to copy package name** to clipboard
- Auto-labeled: APPanel-main, APPanel-fast, APPanel-freq, APPanel-mem, APPanel-proc, APPanel-medium, APPanel-slow, APPanel-ap, APPanel-action, APPanel-adb, APPanel-ps, APPanel-AP-backend, APPanel-channel-shell, etc.
- Hidden process prefix filtering (e.g., android.), user-customizable

### Settings Editor
- Visual settings.json editor with categories:
  - **Chips**: Processor codename → display name
  - **Packages**: Package name → app name
  - **Autostart**: Toggle switches, auto-writes to ~/.bashrc
  - **Collection Speed**: Per-channel multiplier (0.25x~4x)
  - **Hidden Processes**: Filter by prefix
- Inline editing, add/delete entries
- **📱 Quick Add**: One-click add current foreground app to mapping
- JSON validation, auto-reload on save

### Settings Extra Pages
- **Kill-Process**: Dedicated process management page with search filter + KILL button (am force-stop & kill), CPU descending default
- **Version**: Local git hash + remote latest version check, manual update trigger
- **Port Config**: Customize Flask/WebSocket/AP/ADB/ScreenOff ports
- **Restart**: One-click restart APPanel + kill proot-distro ubuntu

### Other Features
- **WebSocket Diff Push**: Only send changed fields, full sync every 10 cycles for reliability
- **Render Debounce**: 50ms debounce on WS messages
- **Process Table HTML Cache**: Skip DOM rebuild when ps_raw unchanged
- ~~**Live Collection Frequency Display**~~: Removed due to inaccurate calculation and performance overhead
- **Click-to-edit title**
- **Temperature hover warnings**: CPU >70°C / Battery >40°C
- **Dark/Light theme toggle**, no refresh needed

---

## Deployment

### Prerequisites

1. **Termux** (F-Droid version)
2. **Install packages** (run `termux-change-repo` first for faster mirrors in China):
   ```bash
   pkg update && pkg upgrade -y
   pkg install python android-tools openssh git -y
   pip install flask websockets
   ```
3. **ADB Wireless Debugging**:
   - Enable Developer options → Wireless debugging on phone
   - Pair: `adb pair 127.0.0.1:pairing_port`
   - Connect: `adb connect 127.0.0.1:connection_port`
   - Verify: `adb devices`

### Install

```bash
git clone https://github.com/YuCould/APPanel.git ~/APPanel
cd ~/APPanel
python dashboard.py
```

Open `http://<phone-ip>:20080` in browser.

### Autostart

<small>Root required, otherwise ADB re-pairing needed after reboot.</small>

Settings → Autostart → toggle on → Save, auto-writes to `~/.bashrc`.

### AP Backend

Works with [AzurPilot](https://github.com/wess09/AzurPilot) deployed inside proot-distro ubuntu. Settings → Autostart → enable **AP Backend**.

### Screen Off Service

[ScreenOff](https://github.com/WuDi-ZhanShen/ScreenOff) (clone: [YuCould/ScreenOff-APPanel](https://github.com/YuCould/ScreenOff-APPanel)) — turn off OLED screen while keeping apps running. Requires [Shizuku](https://shizuku.rikka.app/) permissions. Default port 20000.

---

## Architecture

### 8-Channel Persistent ADB Shells

Each channel has an independent ADB shell + local bash --norc process + threading.Lock. The frontend labels ADB shells as `APPanel-channel-collect` and local bash as `APPanel-channel-shell`:

| Channel | Collectors | Base Interval | Speed Multiplier |
|---------|-----------|---------------|------------------|
| `fast` | CPU jiffies + network bytes + AP process | 2s | fast |
| `freq` | CPU core frequency | 2s | fast |
| `mem` | Memory (/proc/meminfo) | 2s | fast |
| `proc` | Process list (ps -e) | 2s | fast |
| `medium` | Battery + foreground app + CPU temp | 10s | medium |
| `slow` | Storage (df) | 30s | slow |
| `ap` | AP ping + IP + uptime + model | 10~60s | slow |
| `action` | KILL operations | on-demand | - |

### Data Flow

```
Collector threads → _sd(shared dict) → Broadcast(0.5s) → diff → WebSocket → Object.assign → render(50ms debounce)
```

- Broadcast thread syncs `_sd` to `CACHE` every 0.5s, computes diff, sends only changed fields
- Full push every 10 cycles for reliability
- Frontend uses `Object.assign` for incremental merge, 50ms debounced `render()`

### Collection Methods

All data collected via **8 persistent ADB/Local shells**:

| Data | Channel | Command | Interval |
|------|---------|---------|----------|
| CPU usage | `fast` ADB | `cat /proc/stat` → jiffies diff | 2s |
| Network traffic | `fast` ADB | `cat /proc/net/dev` parse `wlan0` | 2s |
| CPU freq | `freq` ADB | sysfs `scaling_cur_freq` | 2s |
| CPU model | `ap` local | `getprop ro.board.platform` | 60s |
| Memory | `mem` ADB | `cat /proc/meminfo` | 2s |
| Storage | `slow` local | `df /data` | 30s |
| Battery+fg | `medium` ADB | `dumpsys battery` + `dumpsys window` | 10s |
| CPU temp | `medium` local | thermal_zone files | 10s |
| Process list | `proc` ADB | `ps -e -o pid,pcpu,rss,args` | 2s |
| AP process | `fast` local | `ps \| grep gui.py` | 2s |
| AP ping+IP | `ap` ADB | TCP check + `ip addr show wlan0` | 10s |

### Performance

- **CPU**: Depends on processor performance; higher-end CPUs use less. Fast collection ~5%~20% single core, other channels <1%
- **Memory**: Main process ~30MB + 8 ADB shells ~64MB (8MB ea.) + 8 local bash ~32MB (4MB ea.)
- **Network**: ~30KB/push per client (85% is ps_raw), diff push ~hundreds of bytes

---

## File Reference

| File | Description |
|:-----|:------------|
| `dashboard.py` | Entry point |
| `server.py` | Flask + WebSocket server |
| `page.html` | Single-page frontend (CSS+JS inline) |
| `settings.json` | Chip/app/autostart/speed/hidden config |
| `config.py` | Port and address config |
| `collectors/adb_shell.py` | 8-channel persistent ADB/Local shell manager |
| `collectors/base.py` | Collector utilities (channel wrappers, thread launcher) |
| `collectors/runner.py` | Collector starter, channel assignment |
| `collectors/broadcast.py` | Diff broadcast thread |
| `collectors/hot_protect.py` | Overheat protection (≥50°C 15min auto-kill) |
| `collectors/fast_bundle.py` | CPU + network + AP process |
| `collectors/cpu.py` | CPU frequency + model |
| `collectors/memory.py` | Memory |
| `collectors/processes.py` | Process list (backend hidden-proc filtering) |
| `collectors/battery.py` | Battery + foreground app |
| `collectors/temperature.py` | CPU temperature |
| `collectors/storage.py` | Storage |
| `collectors/ap_ip.py` | AP ping + IP + uptime |
| `collectors/ws.py` | WebSocket client manager |
| `collectors/shared.py` | Shared state (_sd, _CPU_MAP, locks) |
| `routes/misc.py` | Misc routes (index, API, restart, version, kill-ubuntu) |
| `routes/config_routes.py` | Settings API + autostart .bashrc generator |
| `startup.sh` | Manual startup script (sshd + APPanel) |
| `start_ap.sh` | AP backend launcher (proot-distro ubuntu) |

## settings.json

Managed via Settings page. Structure:

```json
{
  "chips": { "kona": "Snapdragon 865" },
  "packages": { "com.tencent.mm": "WeChat" },
  "autostart": { "sshd": true, "dashboard": true, "ap_backend": false, "hot_protect": true, "fix_adb_port": false },
  "collect_speeds": { "fast": 1.0, "medium": 1.0, "slow": 1.0 },
  "hidden_procs": { "android.": "" }
}
```
