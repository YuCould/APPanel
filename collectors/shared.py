#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集器共享状态模块
持有全局配置映射、锁、缓存等，供所有采集器和路由引用。
"""
import os, json, threading

from logger import info, error, warn

# ── settings.json 路径与内存映射 ──
_CPU_MAP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")
_CPU_MAP = {"chips": {}, "implementers": {}, "vendor_keywords": {}, "packages": {}}

def _load_settings() -> bool:
    """从 settings.json 加载映射到内存"""
    global _CPU_MAP
    try:
        if os.path.exists(_CPU_MAP_PATH):
            with open(_CPU_MAP_PATH, encoding="utf-8") as _f:
                _m = json.load(_f)
                _CPU_MAP["chips"] = _m.get("chips", {})
                _CPU_MAP["implementers"] = _m.get("implementers", {})
                _CPU_MAP["vendor_keywords"] = _m.get("vendor_keywords", {})
                _CPU_MAP["packages"] = _m.get("packages", {})
                _CPU_MAP["autostart"] = _m.get("autostart", {})
                info(f"已加载 {len(_CPU_MAP['chips'])} 个芯片映射, {len(_CPU_MAP['packages'])} 个应用映射")
                return True
    except Exception as _e:
        error(f"映射文件加载失败: {_e}")
    return False

# 启动时加载，若无文件则用内置默认
if not _load_settings():
    _CPU_MAP["chips"] = {
        "kona": "骁龙 865", "lahaina": "骁龙 888", "waipio": "骁龙 8 Gen 1", "diwali": "骁龙 8+ Gen 1",
        "kalama": "骁龙 8 Gen 2", "pineapple": "骁龙 8 Gen 3", "sun": "骁龙 8 Gen 4",
        "parrot": "骁龙 6 Gen 1", "bengal": "骁龙 662", "holi": "骁龙 480", "punjab": "骁龙 695",
        "shima": "骁龙 778G+", "yupik": "骁龙 778G+", "taro": "骁龙 7 Gen 1", "crow": "骁龙 7+ Gen 3",
        "lito": "骁龙 765G", "atoll": "骁龙 730G",
        "sm8650": "骁龙 8 Gen 3", "sm8550": "骁龙 8 Gen 2", "sm8475": "骁龙 8+ Gen 1", "sm8450": "骁龙 8 Gen 1",
        "sm8350": "骁龙 888", "sm8250": "骁龙 865", "sm8150": "骁龙 855", "sm845": "骁龙 8 Gen 1",
        "sm6375": "骁龙 695", "sm6225": "骁龙 680", "sm7325": "骁龙 778G", "sm7250": "骁龙 765G",
        "sm7150": "骁龙 730G", "sm6350": "骁龙 690", "sm6250": "骁龙 665", "sm4350": "骁龙 480",
        "sm4250": "骁龙 460", "sm6115": "骁龙 662", "sm6125": "骁龙 665",
        "sdm845": "骁龙 845", "sdm710": "骁龙 710", "sdm660": "骁龙 660", "sdm670": "骁龙 670",
        "sdm675": "骁龙 675", "sdm632": "骁龙 632", "sdm636": "骁龙 636", "sdm630": "骁龙 630",
        "sdm450": "骁龙 450", "sdm439": "骁龙 439", "sdm435": "骁龙 435", "sdm430": "骁龙 430",
        "msm8998": "骁龙 835", "msm8996": "骁龙 820", "msm8994": "骁龙 810", "msm8976": "骁龙 652",
        "msm8953": "骁龙 625", "msm8940": "骁龙 435", "msm8937": "骁龙 430", "msm8917": "骁龙 425",
        "mt6983": "天玑 9000", "mt6985": "天玑 9200", "mt6989": "天玑 9300", "mt6991": "天玑 9400",
        "mt6895": "天玑 8100", "mt6893": "天玑 1200", "mt6891": "天玑 1100", "mt6879": "天玑 8000",
        "mt6877": "天玑 1200", "mt6873": "天玑 1000+", "mt6853": "天玑 720", "mt6833": "天玑 810",
        "mt6785": "天玑 G95", "mt6768": "天玑 G80", "mt6765": "天玑 G70", "mt6781": "天玑 6100+",
        "mt6739": "天玑 A22", "kirin9000": "麒麟 9000", "kirin990": "麒麟 990", "kirin985": "麒麟 985",
        "kirin980": "麒麟 980", "kirin970": "麒麟 970", "kirin960": "麒麟 960", "kirin950": "麒麟 950",
        "kirin810": "麒麟 810", "kirin820": "麒麟 820", "kirin710": "麒麟 710", "kirin659": "麒麟 659",
        "exynos2200": "Exynos 2200", "exynos2100": "Exynos 2100", "exynos990": "Exynos 990",
        "exynos9820": "Exynos 9820", "exynos9810": "Exynos 9810", "exynos8895": "Exynos 8895",
        "gs201": "Tensor G2", "gs101": "Tensor",
    }
    _CPU_MAP["implementers"] = {"0x51": "高通", "0x48": "华为", "0x53": "三星", "0x69": "英特尔", "0x61": "苹果", "0x42": "博通"}
    _CPU_MAP["vendor_keywords"] = {
        "qualcomm": "高通", "qcom": "高通", "mediatek": "联发科", "mtk": "联发科",
        "exynos": "三星", "samsung": "三星", "kirin": "华为", "hisilicon": "华为",
        "apple": "苹果", "rockchip": "瑞芯微", "unisoc": "紫光展锐", "intel": "英特尔", "bcm": "博通",
    }
    _CPU_MAP["packages"] = {"python3": "APPanel", "python": "APPanel", "dashboard.py": "APPanel"}
    _CPU_MAP["autostart"] = {
        "sshd": True,
        "dashboard": True,
        "ap_backend": True,
    }
    try:
        with open(_CPU_MAP_PATH, "w", encoding="utf-8") as _f:
            json.dump(_CPU_MAP, _f, indent=2, ensure_ascii=False)
    except (OSError, TypeError):
        pass

# ── 系统应用前缀（排除，不自动加入映射） ──
SYS_PREFIXES = [
    "com.google.android.",
    # 以下不排除
    # "android.", "com.android.",  "com.google.", "com.qualcomm.",
    # "com.mediatek.", "com.qti.", "com.samsung.android.", "com.miui.", "com.xiaomi.",
    # "com.oneplus.", "com.oppo.", "com.vivo.", "com.huawei.", "com.coloros.",
    # "com.realme.", "com.asus.", "com.sony.", "com.lge.", "com.sec.android.",
    # # 国产厂商系统组件
    # "com.oplus.", "com.heytap.", "com.nearme.",
    # "com.iqoo.", "com.funtouch.",
    # "com.zte.", "com.nubia.",
    # "com.lenovo.", "com.motorola.",
]

# ── 设备一次性信息 ──
LOSTAT = {"md": "?", "av": "?", "cc": "?", "cf": "?", "cm": "?", "dn": "?"}

# ── 运行时状态 ──
_ap_ever_online = False
_pkg_label_cache = {}       # 包名→应用名称缓存
_data_lock = threading.Lock()
_settings_dirty = False     # 自动学习脏标记
_sd = {"screen_on": True}   # 共享数据字典（采集器写入，广播线程读取）

def _mark_dirty() -> None:
    """标记 settings 有变动，触发自动保存"""
    global _settings_dirty
    _settings_dirty = True


def _auto_save_settings() -> None:
    """将内存中的 _CPU_MAP 自动保存到 settings.json（保留注释字段）"""
    global _settings_dirty
    if not _settings_dirty:
        return
    try:
        if os.path.exists(_CPU_MAP_PATH):
            with open(_CPU_MAP_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = {}
        for key in ("chips", "packages", "implementers", "vendor_keywords"):
            existing[key] = _CPU_MAP.get(key, {})
        with open(_CPU_MAP_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        _settings_dirty = False
        total = sum(len(v) for v in existing.values() if isinstance(v, dict))
        info(f"settings.json 已自动保存 ({total} 条映射)")
    except Exception as e:
        error(f"自动保存失败: {e}")
