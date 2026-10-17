# -*- coding: utf-8 -*-
"""
一键切换屏幕方向（横屏 <-> 竖屏），仅支持 Windows，纯标准库实现。

用法：
    python rotate_screen.py                 # 交互式菜单：选择屏幕和操作
    python rotate_screen.py portrait        # 主屏强制竖屏
    python rotate_screen.py landscape       # 主屏强制横屏
    python rotate_screen.py 90              # 主屏旋转到指定角度(0/90/180/270)
    python rotate_screen.py --angles 90,0 --device 2   # 在 90 和 0 两个角度间切换
    python rotate_screen.py portrait --device 2   # 只操作第 2 台显示器
    python rotate_screen.py --all           # 切换所有显示器的方向
    python rotate_screen.py --list          # 列出所有已连接的显示器
"""

import ctypes
import sys
from ctypes import wintypes

# ---------------- 常量 ----------------
ENUM_CURRENT_SETTINGS = -1
CDS_UPDATEREGISTRY = 0x00000001

DM_DISPLAYORIENTATION = 0x00000080
DM_BITSPERPEL = 0x00040000
DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000
DM_DISPLAYFREQUENCY = 0x00400000

CDS_TEST = 0x00000002

DISP_CHANGE_SUCCESSFUL = 0
DISP_CHANGE_RESTART = 1
DISP_CHANGE_FAILED = -1
DISP_CHANGE_BADMODE = -2
DISP_CHANGE_NOTUPDATED = -3
DISP_CHANGE_BADFLAGS = -4
DISP_CHANGE_BADPARAM = -5
DISP_CHANGE_BADDUALVIEW = -6

DISP_CHANGE_MSG = {
    0: "成功",
    1: "成功，但需要重启后生效",
    -1: "显示驱动切换失败",
    -2: "显示模式不受支持(BADMODE)",
    -3: "无法写入注册表(NOTUPDATED)",
    -4: "参数标志无效(BADFLAGS)",
    -5: "参数无效(BADPARAM)",
    -6: "多显示器视图设置失败(BADDUALVIEW)",
}

DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001

DMDO_DEFAULT = 0   # 横屏
DMDO_90 = 1        # 竖屏（顺时针 90°）
DMDO_180 = 2       # 横屏倒置
DMDO_270 = 3       # 竖屏（逆时针 90°）

ORIENTATION_NAME = {
    DMDO_DEFAULT: "横屏",
    DMDO_90: "竖屏(90°)",
    DMDO_180: "横屏(180°)",
    DMDO_270: "竖屏(270°)",
}

# 用户输入的角度 -> DMDO 值
ANGLE_TO_DMDO = {
    0: DMDO_DEFAULT,
    90: DMDO_90,
    180: DMDO_180,
    270: DMDO_270,
}

# ---------------- 结构体 ----------------
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_uint),
        ("dmPosition", POINT),
        ("dmDisplayOrientation", ctypes.c_int),
        ("dmDisplayFixedOutput", ctypes.c_uint),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", ctypes.c_uint),
        ("dmPelsWidth", ctypes.c_uint),
        ("dmPelsHeight", ctypes.c_uint),
        ("dmDisplayFlags", ctypes.c_uint),
        ("dmDisplayFrequency", ctypes.c_uint),
        ("dmICMMethod", ctypes.c_uint),
        ("dmICMIntent", ctypes.c_uint),
        ("dmMediaType", ctypes.c_uint),
        ("dmDitherType", ctypes.c_uint),
        ("dmReserved1", ctypes.c_uint),
        ("dmReserved2", ctypes.c_uint),
        ("dmPanningWidth", ctypes.c_uint),
        ("dmPanningHeight", ctypes.c_uint),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_uint32),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", ctypes.c_uint32),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


user32 = ctypes.windll.user32

# 显式声明参数类型（关键：不声明时 ctypes 不校验参数个数，多传参数会导致 BADPARAM）
user32.ChangeDisplaySettingsExW.argtypes = [
    wintypes.LPCWSTR, ctypes.POINTER(DEVMODEW), wintypes.DWORD, wintypes.LPVOID]
user32.ChangeDisplaySettingsExW.restype = wintypes.LONG
user32.ChangeDisplaySettingsW.argtypes = [ctypes.POINTER(DEVMODEW), wintypes.DWORD]
user32.ChangeDisplaySettingsW.restype = wintypes.LONG


def apply_mode(device_name, dm):
    """
    按优先级尝试三种应用方式，返回 (返回码, 说明)：
      1) CDS_TEST 预验证 + CDS_UPDATEREGISTRY 持久化（规范路径，多数机器可用）
      2) flags=0 动态生效（部分驱动拒绝上面的 flags 但允许 0，且能精确指定显示器）
      3) ChangeDisplaySettingsW 旧 API（作用于当前主显示器，可能不是所选屏幕）
    """
    if user32.ChangeDisplaySettingsExW(device_name, ctypes.byref(dm), CDS_TEST, None) == DISP_CHANGE_SUCCESSFUL:
        r = user32.ChangeDisplaySettingsExW(device_name, ctypes.byref(dm), CDS_UPDATEREGISTRY, None)
        if r == DISP_CHANGE_SUCCESSFUL:
            return r, "已写入注册表"
    r = user32.ChangeDisplaySettingsExW(device_name, ctypes.byref(dm), 0, None)
    if r == DISP_CHANGE_SUCCESSFUL:
        return r, "动态生效（注销/重启后恢复默认）"
    r = user32.ChangeDisplaySettingsW(ctypes.byref(dm), CDS_UPDATEREGISTRY)
    return r, "已回退到旧 API（可能作用于主显示器而非所选屏幕）"


def list_displays():
    """返回 [(DeviceName, DeviceString), ...]，仅包含连接到桌面的显示器。"""
    devices = []
    i = 0
    while True:
        dd = DISPLAY_DEVICEW()
        dd.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(dd), 0):
            break
        if dd.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP:
            devices.append((dd.DeviceName, dd.DeviceString))
        i += 1
    return devices


def get_current_settings(device_name):
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if not user32.EnumDisplaySettingsW(device_name, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
        return None
    return dm


def snapshot():
    """记录所有显示器的当前状态 {DeviceName: (描述, 方向, 宽, 高)}，用于前后对比"""
    state = {}
    for name, desc in list_displays():
        d = get_current_settings(name)
        if d is not None:
            state[name] = (desc, d.dmDisplayOrientation, d.dmPelsWidth, d.dmPelsHeight)
    return state


def rotate(device_name, mode=None):
    """
    mode: None=切换(保持旋转的"侧": 横0↔竖90, 横180↔竖270),
          "portrait"/"landscape"=强制竖/横屏,
          0/90/180/270=旋转到指定角度,
          (角度A, 角度B)=在两个指定角度之间切换（当前是 A 则去 B，反之去 A，都不是则去 A）
    返回 (success, message)
    """
    dm = get_current_settings(device_name)
    if dm is None:
        return False, "无法读取当前显示设置"

    current = dm.dmDisplayOrientation
    is_landscape_now = current in (DMDO_DEFAULT, DMDO_180)

    if isinstance(mode, tuple):
        angle_a, angle_b = mode
        for x in (angle_a, angle_b):
            if x not in ANGLE_TO_DMDO:
                return False, "无效的角度 %d（仅支持 0/90/180/270）" % x
        if current == ANGLE_TO_DMDO[angle_a]:
            new_orientation = ANGLE_TO_DMDO[angle_b]
        elif current == ANGLE_TO_DMDO[angle_b]:
            new_orientation = ANGLE_TO_DMDO[angle_a]
        else:
            new_orientation = ANGLE_TO_DMDO[angle_a]
    elif mode is None:
        # 切换：在同一"侧"内往返，保证再切一次能回到原状态
        new_orientation = {
            DMDO_DEFAULT: DMDO_90,
            DMDO_90: DMDO_DEFAULT,
            DMDO_180: DMDO_270,
            DMDO_270: DMDO_180,
        }.get(current, DMDO_90)
    elif isinstance(mode, int):
        dmdo = ANGLE_TO_DMDO.get(mode)
        if dmdo is None:
            return False, "无效的角度 %d（仅支持 0/90/180/270）" % mode
        if dmdo == current:
            return True, "已经是 %s，无需切换" % ORIENTATION_NAME[current]
        new_orientation = dmdo
    elif mode == "portrait":
        if current in (DMDO_90, DMDO_270):
            return True, "已经是竖屏，无需切换"
        new_orientation = DMDO_90
    else:
        if current in (DMDO_DEFAULT, DMDO_180):
            return True, "已经是横屏，无需切换"
        new_orientation = DMDO_DEFAULT

    width, height = dm.dmPelsWidth, dm.dmPelsHeight
    will_be_portrait = new_orientation in (DMDO_90, DMDO_270)
    # 横竖互换时才需要交换宽高
    if will_be_portrait != (not is_landscape_now):
        width, height = height, width

    # 候选模式 1：当前模式，仅交换宽高、改变方向（驱动保留其余参数）
    candidates = []
    cand = DEVMODEW.from_buffer_copy(dm)
    cand.dmPelsWidth = width
    cand.dmPelsHeight = height
    cand.dmDisplayOrientation = new_orientation
    cand.dmFields = DM_DISPLAYORIENTATION | DM_PELSWIDTH | DM_PELSHEIGHT
    candidates.append(cand)

    # 候选模式 2..n：枚举驱动支持的所有模式，找宽高互换、色深相同的，优先刷新率接近的
    i = 0
    same_freq, other_freq = [], []
    while user32.EnumDisplaySettingsW(device_name, i, ctypes.byref(dm)):
        if (dm.dmPelsWidth == height and dm.dmPelsHeight == width
                and dm.dmBitsPerPel == candidates[0].dmBitsPerPel):
            cand2 = DEVMODEW.from_buffer_copy(dm)
            cand2.dmDisplayOrientation = new_orientation
            cand2.dmFields = (DM_DISPLAYORIENTATION | DM_BITSPERPEL | DM_PELSWIDTH
                              | DM_PELSHEIGHT | DM_DISPLAYFREQUENCY)
            if dm.dmDisplayFrequency == candidates[0].dmDisplayFrequency:
                same_freq.append(cand2)
            else:
                other_freq.append(cand2)
        i += 1
    candidates.extend(same_freq)
    candidates.extend(other_freq)

    before = snapshot()

    last_result = DISP_CHANGE_FAILED
    last_note = ""
    for cand in candidates:
        last_result, last_note = apply_mode(device_name, cand)
        if last_result != DISP_CHANGE_SUCCESSFUL:
            continue
        # 应用后验证：确认变化确实发生在所选屏幕上
        after = snapshot()
        cur = after.get(device_name)
        if cur and cur[1] == new_orientation:
            return True, "已切换为 %s，分辨率 %dx%d（%s）" % (
                ORIENTATION_NAME.get(new_orientation, str(new_orientation)),
                cur[2], cur[3], last_note)
        # 目标屏幕没变，找出实际被旋转的屏幕并明确告知
        for name, s in after.items():
            if before.get(name) != s:
                return True, "警告：所选屏幕未变化，实际被旋转的是「%s」（%s）。" \
                    "本机 Ex API 指定显示器失败，已回退到旧 API" % (s[0], last_note)

    msg = DISP_CHANGE_MSG.get(last_result, "未知错误码 %d" % last_result)
    return False, "切换失败（%s）。若提示模式不受支持，可在显卡控制面板中确认允许旋转显示" % msg


def show_displays():
    """打印显示器列表，返回 [(DeviceName, DeviceString), ...]"""
    devices = list_displays()
    if not devices:
        print("未检测到显示器")
        return devices
    print("检测到以下显示器：")
    for idx, (name, desc) in enumerate(devices, 1):
        d = get_current_settings(name)
        if d is not None:
            print("  [%d] %-32s 当前: %s  %dx%d" % (
                idx, desc, ORIENTATION_NAME.get(d.dmDisplayOrientation, "?"),
                d.dmPelsWidth, d.dmPelsHeight))
        else:
            print("  [%d] %-32s (无法读取当前设置)" % (idx, desc))
    return devices


def interactive_menu():
    """交互式选择屏幕与操作"""
    devices = show_displays()
    if not devices:
        return 1

    choice = input("\n请选择屏幕编号 (回车=1, a=全部, q=退出): ").strip().lower()
    if choice in ("q", "quit", "exit"):
        return 0
    if choice in ("a", "all"):
        targets = [name for name, _ in devices]
    else:
        try:
            idx = int(choice) if choice else 1
        except ValueError:
            print("错误: 请输入数字编号")
            return 1
        if not 1 <= idx <= len(devices):
            print("错误: 编号超出范围 1-%d" % len(devices))
            return 1
        targets = [devices[idx - 1][0]]

    action = input("操作 (回车=切换横竖, p=竖屏, l=横屏, 或输入角度 0/90/180/270): ").strip().lower()
    mode = None
    if action in ("p", "portrait", "竖屏"):
        mode = "portrait"
    elif action in ("l", "landscape", "横屏"):
        mode = "landscape"
    elif action in ("0", "90", "180", "270"):
        mode = int(action)

    print()
    failed = 0
    for name in targets:
        ok, msg = rotate(name, mode)
        print("[%s] %s" % ("成功" if ok else "失败", msg))
        if not ok:
            failed += 1
    return 1 if failed else 0


def main(argv):
    if sys.platform != "win32":
        print("错误：本程序仅支持 Windows")
        return 1

    # 先剔除 --device N 这一对，再提取位置参数（否则 N 会被误当成模式参数）
    rest = list(argv[1:])
    if "--device" in rest:
        i = rest.index("--device")
        del rest[i:i + 2]
    angles = None
    if "--angles" in rest:
        i = rest.index("--angles")
        try:
            raw = rest[i + 1].replace("|", ",").split(",")
            if len(raw) != 2:
                raise ValueError
            angles = (int(raw[0]), int(raw[1]))
        except (ValueError, IndexError):
            print("错误: --angles 需要两个角度，用逗号分隔，如 --angles 90,0")
            return 1
        del rest[i:i + 2]
    positional = [a for a in rest if not a.startswith("-")]
    mode = None
    if positional and positional[0].lower() in ("portrait", "vertical", "竖屏"):
        mode = "portrait"
    elif positional and positional[0].lower() in ("landscape", "horizontal", "横屏"):
        mode = "landscape"
    elif positional and positional[0] in ("0", "90", "180", "270"):
        mode = int(positional[0])
    elif positional:
        print(__doc__)
        return 1
    if mode is None and angles is not None:
        mode = angles

    if "--list" in argv:
        show_displays()
        return 0

    if not argv[1:]:
        # 无参数：进入交互式选择菜单
        try:
            return interactive_menu()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            return 1

    devices = list_displays()
    if not devices:
        print("未检测到显示器")
        return 1

    if "--all" in argv:
        targets = [name for name, _ in devices]
    else:
        device_index = 1
        if "--device" in argv:
            try:
                device_index = int(argv[argv.index("--device") + 1])
            except (ValueError, IndexError):
                print("错误: --device 后需要跟显示器编号（见 --list）")
                return 1
        if not 1 <= device_index <= len(devices):
            print("错误: 显示器编号超出范围 1-%d" % len(devices))
            return 1
        targets = [devices[device_index - 1][0]]

    failed = 0
    for name in targets:
        ok, msg = rotate(name, mode)
        print("[%s] %s" % ("成功" if ok else "失败", msg))
        if not ok:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
