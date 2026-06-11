package com.apanel;

import android.os.Build;
import android.os.IBinder;
import android.view.SurfaceControl;

/**
 * 熄屏不锁频工具 — 跨 Android 版本兼容
 *
 * 编译：
 *   1. 在电脑上安装 Android SDK，找到 android.jar（如 ~/Android/Sdk/platforms/android-34/android.jar）
 *   2. 编译：
 *      javac -bootclasspath android.jar -d . ScreenEscrcpy.java
 *   3. 打包 dex：
 *      d8 --lib android.jar com/apanel/ScreenEscrcpy.class
 *      或 dalvik-exchange:
 *      dx --dex --output=escrcpy.dex com/apanel/ScreenEscrcpy.class
 *   4. 推送：
 *      adb push escrcpy.dex /data/local/tmp/
 *
 * 使用（mode: 0=熄屏, 2=亮屏）：
 *   app_process -Djava.class.path=/data/local/tmp/escrcpy.dex \
 *       /data/local/tmp com.apanel.ScreenEscrcpy 0
 *
 * 原理：
 *   Android  9 及以下：SurfaceControl.getBuiltInDisplay(0)
 *   Android 10~13：   SurfaceControl.getPhysicalDisplayIds()
 *   Android 14+：     尝试 SurfaceControl，失败则用 DisplayControl
 */
public class ScreenEscrcpy {

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: ScreenEscrcpy <mode>  (0=off, 2=on)");
            System.exit(1);
        }

        int mode;
        try {
            mode = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.err.println("Invalid mode: " + args[0]);
            System.exit(1);
            return;
        }

        IBinder displayToken = null;
        int apiLevel = Build.VERSION.SDK_INT;

        try {
            // ── 获取显示器 Token ──
            if (apiLevel >= 34) {
                // Android 14+：优先用 SurfaceControl，失败则 DisplayControl
                displayToken = getTokenByPhysicalDisplayId_SurfaceControl();
                if (displayToken == null) {
                    displayToken = getTokenByPhysicalDisplayId_DisplayControl();
                }
            } else if (apiLevel >= 29) {
                // Android 10~13
                displayToken = getTokenByPhysicalDisplayId_SurfaceControl();
            } else {
                // Android 9 及以下
                displayToken = getTokenByBuiltInDisplay();
            }

            if (displayToken == null) {
                System.err.println("No display token found");
                System.exit(1);
                return;
            }

            // ── 设置熄屏/亮屏 ──
            SurfaceControl.class
                .getMethod("setDisplayPowerMode", IBinder.class, int.class)
                .invoke(null, displayToken, mode);

            System.out.println("OK");
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }

    /** Android 9 及以下：通过内置显示器 ID 获取 Token */
    private static IBinder getTokenByBuiltInDisplay() throws Exception {
        return (IBinder) SurfaceControl.class
            .getMethod("getBuiltInDisplay", int.class)
            .invoke(null, 0);  // 0 = BUILT_IN_DISPLAY_ID_MAIN
    }

    /** Android 10~13：通过 SurfaceControl 获取物理显示器 Token */
    private static IBinder getTokenByPhysicalDisplayId_SurfaceControl() throws Exception {
        long[] ids = (long[]) SurfaceControl.class
            .getMethod("getPhysicalDisplayIds")
            .invoke(null);
        if (ids == null || ids.length == 0) return null;
        return (IBinder) SurfaceControl.class
            .getMethod("getPhysicalDisplayToken", long.class)
            .invoke(null, ids[0]);
    }

    /** Android 14+：通过 DisplayControl（系统服务）获取物理显示器 Token */
    private static IBinder getTokenByPhysicalDisplayId_DisplayControl() throws Exception {
        Class<?> dc = Class.forName("com.android.server.display.DisplayControl");
        long[] ids = (long[]) dc.getMethod("getPhysicalDisplayIds").invoke(null);
        if (ids == null || ids.length == 0) return null;
        return (IBinder) dc.getMethod("getPhysicalDisplayToken", long.class)
            .invoke(null, ids[0]);
    }
}
