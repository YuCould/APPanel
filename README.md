# APPanel — Android 设备实时监控仪表盘

运行在 **Termux** 中，通过 **Web 页面**实时展示 Android 设备状态。集成了 ADB 无线调试、多线程采集、WebSocket 推送，无需 root 即可实现 CPU/内存/存储/网络/电池/进程等全方位监控。

### 核心特性

- 🖥️ **Web 仪表盘** — Flask + WebSocket 实时推送，桌面/移动端自适应布局
- 📊 **多维度监控** — CPU 占用/频率、内存、存储、网络速率/总流量、电池电量/温度、进程列表
- 🔌 **ADB 无线调试** — 无需 USB 线，通过 ADB 采集设备数据，支持自动固定端口
- 🌙 **熄屏挂机** — 通过 SurfaceControl API 或系统 dream 熄灭屏幕（OLED 像素完全关闭），APP 保持运行不锁频，不影响音乐/下载
- ⚡ **高温保护** — 电池≥50°C 持续 15 分钟自动杀 AP 后端和碧蓝航线进程
- 🔧 **可视化设置** — Web 页面管理芯片映射、应用名映射、自启动开关、端口配置
- 📁 **文件浏览器** — 上传、下载、更名、删除，支持受保护文件锁定
- 🎨 **三主题切换** — 深色/浅色/多彩，实时切换无需刷新
- 🔄 **一键更新** — 版本检测对比，一键 `git pull` 并自动重启
- 🛡️ **自启动守护** — SSH/仪表盘/AP后端/自动熄屏/高温杀进程/固定ADB端口，页面开关即配置

![APPanel 界面预览](index.png)

## 功能

### 仪表盘
- **CPU**：实时占用率（单核 + 多核合计），带动态渐变进度条，左上角显示大小核频率，右上角显示总和
- **内存**：已用/总量显示，百分比进度条，左上角占用内存最大的 3 个进程，右上角对应应用名
- **存储**：已用/总量显示，左上角显示 APPanel 项目目录大小
- **网络**：实时下载/上传速率，Canvas 60fps 贝塞尔曲线图表，180 个采样点；左上角 IPv4 + IPv6，左下角总下载量，右下角总上传量
- **电池**：电量百分比（数字动画过渡），电池温度（>40°C 预警，>50°C 持续 15 分钟自动杀 AP 和碧蓝航线）
- **CPU 温度**：从 thermal_zone 读取，>70°C 显示脱焊风险警告浮动卡片
- **设备信息**：制造商 + 型号 + 代号（仅首次采集）
- **系统版本**：Android API 版本
- **运行时间**：基于服务端启动时间戳本地自动计算，无需反复采集

### 进程管理
- 实时进程列表（CPU > 0.2% 过滤），30 行表格
- 支持按 PID / CPU / 内存 / 应用 / 包名 排序点击
- **点击任意进程行复制包名**到剪贴板
- 自动过滤采集自身的 ADB/shell 进程
- 应用名自动解析（settings.json 映射 + 自动学习）

### 设置编辑器
- 可视化 settings.json 编辑器，支持五大数据分类：
  - **芯片**：处理器代号 → 显示名称
  - **应用**：包名 → 应用名称（支持自动学习）
  - **厂商ID**：CPU implementer → 厂商名称
  - **关键词**：平台关键词 → 芯片代号
  - **自启动**：可视化开关，管理开机自启项，自动写入 ~/.bashrc
- 内联编辑、新增条目、一键删除
- **📱 当前前台按钮**：快速将当前前台 APP 添加到映射
- JSON 格式校验，保存后自动重载

### 设置页附加功能
- **进程管理**：查看所有进程列表（按CPU排序），点击 KILL 按钮可终止进程（支持 am force-stop 和 kill）
- **版本信息**：显示本地 git commit hash 和时间，同时查询远程仓库最新版本，对比提示是否可更新，支持一键拉取更新并自动重启
- **端口配置**：可自定义 APPanel 的 Flask(web)/WebSocket/AP(ALAS)/ADB 端口，保存后重启生效
- **重启**：一键重启 APPanel

### 文件浏览器
- 完整的文件管理：浏览、上传、下载、新建文件夹、更名、删除
- **受保护文件**（dashboard.py, page.html, settings.json 等）红色标注，需「解锁」才能操作
- **下载目录**：独立固定顶栏，点击进入设备的 `~/storage/downloads`
- 解锁状态下受保护文件显示为浅绿色，可更名/删除（force 参数）
- 水滴风格自定义滚动条

### 三主题切换
- **深色**（默认）：`--bg:#1c1e26`，蓝色强调
- **浅色**：纯白背景，GitHub 风格
- **多彩**：渐变彩虹背景，珊瑚色标题

### 自适应布局
- **桌面端**：Flexbox 布局，左侧仪表盘（CPU/内存/存储/网络）+ 右侧进程表
- **移动端**（<768px）：CSS Grid 双列布局，底部固定操作栏，顶部仪表盘缩略

### 其他特性
- **熄屏挂机**：一键熄灭手机屏幕（调节系统熄屏超时），APP 保持运行不锁频，不影响音乐/下载
- **自启动守护**：SSH 服务、APPanel 仪表盘、AP 后端、AP后端运行自动熄屏、电池≥50°C杀碧蓝航线/关闭AP进程、自动固定ADB端口为5555 等守护脚本，通过设置页自启动开关管理
- WebSocket 实时推送（0.1s 间隔）
- 标题点击可自定义修改
- 电池高温保护（50°C 持续 15 分钟自动杀 AP 和碧蓝航线）
- AP 后端存活检测（TCP 端口检测，端口可自定义）
- 无 AP 环境自动隐藏 AP 相关按钮
- 自定义浮动滚动条（水滴交互效果）
- 禁止文本选中，防止误拖选
- 主题实时切换，无需刷新页面
- CPU 温度/电池温度 hover 悬浮提示告警阈值

---

## 部署到新设备

### 前置条件

1. **Termux** 安装（F-Droid 版，不要用 Google Play 版）
2. **Termux 授权存储访问**（首次安装必须）：
   ```bash
   termux-setup-storage
   ```
   手机会弹出存储权限申请，点击**允许**。此命令会在 `~` 下创建 `storage` 软链接，使 Termux 能访问手机内部存储。
3. **安装必要软件包**（如果下载慢可先换源，执行 `termux-change-repo` 选择镜像源）：
   ```bash
   pkg update && pkg upgrade -y
   pkg install python android-tools openssh git -y
   pip install flask websockets
   ```
   > 如果提示 `git` 未找到，请先执行 `pkg install git`。
4. **ADB 无线调试**（读取设备数据需要）：
   - 手机开启「开发者选项」→「无线调试」
   - 使用「配对码配对」，在 Termux 中执行：
     ```bash
     adb pair 127.0.0.1:配对端口   # 例如 adb pair 127.0.0.1:39957
     # 输入手机上显示的配对码
     ```
   - 连接设备：
     ```bash
     adb connect 127.0.0.1:37353   # 使用无线调试界面显示的连接端口
     adb devices                    # 验证是否成功（应输出 "connected"）
     ```

### 安装步骤

**方式一：从 Git 仓库克隆（推荐）**

```bash
# 直接在 Termux 家目录克隆
git clone https://github.com/YuCould/APPanel.git ~/APPanel
cd ~/APPanel
python dashboard.py
```

> 推送更新后，手机上执行 `cd ~/APPanel && git pull` 即可同步最新代码。

**方式二：通过 USB/网盘/分享传输**

```bash
# 1. 在电脑上克隆或下载 APPanel 源码
# 2. 通过以下任一方式传到手机：
#    - USB 数据线连接电脑，复制到手机存储
#    - 网盘（百度云、OneDrive 等）同步到手机
#    - 发送到 Telegram/QQ/微信等，在 Termux 中用 cp 或 mv 复制
# 3. 复制到 Termux 家目录（推荐）：
cp -r /storage/emulated/0/APPanel ~/APPanel

# 4. 进入目录启动
cd ~/APPanel
python dashboard.py
```

> 也可以直接在 `/storage/emulated/0/APPanel` 下运行，但 Termux 对内部存储的访问速度较慢，建议复制到 `~/APPanel`。

**手动更新方式**：将新文件通过文件浏览器上传覆盖，然后重启 APPanel 即可。也可以通过设置页的**版本**标签页一键拉取更新（需要已通过 git clone 部署）。

启动后访问 `http://手机IP:20080` 即可打开仪表盘。
在同一局域网的其他设备上也可访问（如电脑浏览器打开 `http://192.168.x.x:20080`）。

### 设置开机自启动

**方法一：通过页面设置（推荐）**

打开仪表盘 → **设置** → **自启动** 标签页 → 打开 **APPanel 仪表盘** 开关 → **保存**。

后端会自动写入 `~/.bashrc`，下次 Termux 启动时自动运行。不需要手动编辑任何文件。

**方法二：手动编辑 .bashrc**

```bash
nano ~/.bashrc
```

添加以下内容（如果已存在则跳过）：

```bash
# 自启动 - APPanel 仪表盘
if ! pgrep -f 'python.*dashboard.py' > /dev/null; then
    cd ~/APPanel && nohup python3 dashboard.py > ~/dashboard_new.log 2>&1 &
fi
```

**方法三：termux-boot（最可靠）**

1. 安装 [Termux:Boot](https://f-droid.org/packages/com.termux.boot/)
2. 创建启动脚本：
   ```bash
   mkdir -p ~/.termux/boot
   cat > ~/.termux/boot/APPanel.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
sleep 30  # 等待网络就绪
cd ~/APPanel
nohup python3 dashboard.py > ~/dashboard_new.log 2>&1 &
EOF
   chmod +x ~/.termux/boot/APPanel.sh
   ```

**无论哪种方法，都需要确保 Termux 后台运行权限开启：**
- 手机设置 → 应用 → Termux → 电池优化 → **不优化**
- 手机设置 → 应用 → Termux → **允许后台活动**
- **锁住 Termux 后台任务**（多任务界面下拉 Termux 卡片锁定）

### 部署 AP 后端脚本

如果使用 AP 后端（[AzurPilot](https://github.com/wess09/AzurPilot) 等 proot-distro 内的 Python GUI 程序），需要额外部署启动脚本：

```bash
# 1. 复制启动/停止脚本到 ~/
cp ~/APPanel/extras/start_ap.sh ~/
cp ~/APPanel/extras/stop_ap.sh ~/
chmod +x ~/start_ap.sh ~/stop_ap.sh

# 2. 安装 proot-distro 和 Ubuntu 容器
pkg install proot-distro -y
proot-distro install ubuntu

# 3. 在容器内安装 Python 和 uv
proot-distro login ubuntu
# (容器内) apt update && apt install -y python3 python3-pip
# (容器内) pip install uv
# (容器内) exit

# 4. 部署项目到容器（如 [AzurPilot](https://github.com/wess09/AzurPilot)）
# proot-distro login ubuntu
# (容器内) cd /root && git clone https://github.com/wess09/AzurPilot.git && cd AzurPilot && uv sync
# (容器内) exit
```

然后在页面 **设置 → 自启动** 中打开 **AP 后端** 开关保存即可。

### 验证

```bash
pgrep -af dashboard.py          # 检查进程
curl -s http://127.0.0.1:20080/ | head -c 50   # 检查端口
```

看到 `APPanel` 标题即表示成功。

## 数据采集说明

### 采集架构

后端由 **10 个独立采集线程 + 1 个广播线程**组成，各线程错开启动、互不阻塞：

```
┌─ 线程1: CPU + 网络 + 前台应用 ──── 每 2 秒 ── 单次 ADB 捆绑调用
├─ 线程2: 大小核频率 ─────────────── 每 2 秒 ── 本地 sysfs
├─ 线程3: 电池电量/温度 ──────────── 每 10 秒 ─ ADB dumpsys battery
├─ 线程4: CPU 温度 ──────────────── 每 10 秒 ─ thermal_zone 本地读取
├─ 线程5: 内存 ──────────────────── 每 10 秒 ─ /proc/meminfo
├─ 线程6: 存储 ──────────────────── 每 30 秒 ─ df -h /data
├─ 线程7: AP+IP+运行时间 ─────────── 每 10 秒 ─ socket + netstat + uptime
├─ 线程8: 进程列表 ───────────────── 每 10 秒 ─ ADB ps
├─ 线程9: CPU 型号 ──────────────── 每 60 秒 ─ LOSTAT + 芯片映射
├─ 线程10: 自动保存 settings.json ── 每 30 秒 ─ 自动学习后持久化
│
└─ 线程11: 广播 ─────────────────── 每 0.1 秒 ─ WebSocket 推送
```

各线程启动时间错开 0.2~7 秒，避免同时突发。

### 采集方式详情

| 数据 | 采集方式 | 来源 | 间隔 |
|------|----------|------|------|
| CPU 占用率 | `adb shell cat /proc/stat` → 计算 idle 差值 | ADB | 2 秒 |
| 网络流量 | 同一次 ADB 调用中解析 `wlan0` 收发字节 | ADB | 2 秒 |
| 前台应用 | 同一次 ADB 调用中获取当前焦点窗口 | ADB | 2 秒 |
| CPU 大小核频率 | 遍历 `cpu*/cpufreq/scaling_cur_freq`，前半=小核平均，后半=大核平均 | 本地 sysfs | 2 秒 |
| CPU 型号 | `getprop ro.board.platform` + `CPU implementer` + 芯片映射表 | 本地 + ADB | 60 秒 |
| 内存 | `cat /proc/meminfo` → MemTotal / MemAvailable | 本地文件 | 10 秒 |
| 存储 | `df -h /data` | 本地命令 | 30 秒 |
| 电池电量/温度 | `adb shell dumpsys battery` | ADB | 10 秒 |
| CPU 温度 | `/sys/class/thermal/thermal_zone*/temp` | 本地文件 | 10 秒 |
| 进程列表 | `adb shell ps -e -o pid,pcpu,rss,args` | ADB | 10 秒 |
| 设备信息 | `getprop ro.product.*` | 本地命令 | 仅首次 |
| AP 后端存活 | TCP 端口检测 (`127.0.0.1:22267`) | 本地 socket | 10 秒 |

### 性能占用

直接在 Android 设备的 Termux 中运行，10 个采集线程独立并行：

- **CPU 占用**：约 **1% ~ 3%**（单核）
- **内存占用**：约 **20 ~ 35 MB**
- **网络**：仅局域网 WebSocket 推送，每轮数据包约 2~10 KB
- **电池影响**：可忽略不计

> ADB 无线调试模式下，数据通过 loopback（127.0.0.1:5555）传输，不走外部网络。

## settings.json 配置

`settings.json` 存储芯片映射、应用名称映射等配置，可通过页面 **设置** 按钮可视化编辑。

### 结构

```json
{
  "说明": "APPanel 设置文件，通过页面上的「设置」按钮编辑，修改后自动生效",
  "提示_chips": "芯片代号→处理器名映射",
  "提示_packages": "应用包名→中文名映射，不在列表中的应用会自动学习加入",

  "chips": {
    "kona": "骁龙 865",
    "lahaina": "骁龙 888",
    "kalama": "骁龙 8 Gen 2"
  },
  "packages": {
    "com.tencent.mm": "微信",
    "com.ss.android.ugc.aweme": "抖音",
    "python3": "APPanel"
  },
  "implementers": {
    "0x51": "高通"
  },
  "vendor_keywords": {
    "qcom": "kona"
  }
}
```

### 自动学习

自动学习功能会实时将未知数据补充到映射表中，**每 30 秒自动保存**到 `settings.json`，重启不丢失。

| 学习内容 | 触发条件 | 说明 |
|:---------|:---------|:-----|
| **应用包名** | 前台切换 / 进程列表扫描 | 非系统应用的未知包名自动加入 `packages` 映射 |
| **CPU 芯片** | 每 60 秒检测 | 未知芯片代号自动加入 `chips` 映射 |
| **CPU 厂商** | 每 60 秒检测 | 未知 implementer 自动加入 `implementers` 映射 |

> 系统应用前缀（`com.android.`、`com.google.` 等）不会被自动学习。

## 文件说明

| 文件 | 说明 |
|:----|:-----|
| `dashboard.py` | 主后端程序（Flask + WebSocket + 多线程采集） |
| `page.html` | 前端页面（CSS + JavaScript 单页应用） |
| `settings.json` | 芯片/应用映射配置 |
| `favicon.ico` | 网页图标 |
| `requirements.txt` | Python 依赖 |
| `README.md` | 本说明文档 |
| `extras/start_ap.sh` | AP 后端启动脚本（proot-distro + [AzurPilot](https://github.com/wess09/AzurPilot)） |
| `extras/stop_ap.sh` | AP 后端停止脚本 |
