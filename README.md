# 屏幕横竖屏一键切换工具

Windows 下一键切换显示器横屏/竖屏方向的小工具，纯 Python 标准库实现（无需安装第三方包），通过 Windows 显示 API（`ChangeDisplaySettingsExW` 等）直接驱动。

## 文件说明

| 文件 | 作用 |
|---|---|
| `快速切换.bat` | **日常使用**：在预设好的两个角度间一键切换（需先设置） |
| `快速切换设置.bat | **设置**：选择屏幕编号 + 两个切换角度，保存到 `quickswitch.cfg` |
| `切换屏幕方向.bat | **完整菜单版**：列出所有屏幕，临时选择屏幕和操作 |
| `rotate_screen.py | 主程序（也可独立命令行使用） |
| `quickswitch.cfg | 快速切换的配置，格式：`屏幕编号\|角度1\|角度2` |

## 快速上手

1. 双击 **`快速切换设置.bat`**，按提示选择：
   - 屏幕编号（回车保留当前值）
   - 角度1、角度2（可选 `0` / `90` / `180` / `270`）
2. 之后双击 **`快速切换.bat`** 即在两个角度间切换：
   - 当前是角度1 → 切到角度2
   - 当前是角度2 → 切到角度1
   - 当前是其他角度 → 切到角度1

想换屏幕或角度，随时重跑 `快速切换设置.bat`（回车可保留原值）。

## 角度说明

| 角度 | 含义 |
|---|---|
| `0` | 横屏（默认） |
| `90` | 竖屏（顺时针 90°） |
| `180` | 横屏倒置 |
| `270` | 竖屏（逆时针 90°） |

## 命令行用法

```bat
python rotate_screen.py                              :: 交互式菜单（选择屏幕和操作）
python rotate_screen.py portrait                     :: 主屏强制竖屏
python rotate_screen.py landscape                    :: 主屏强制横屏
python rotate_screen.py 90                           :: 主屏旋转到指定角度
python rotate_screen.py --angles 90,0 --device 2     :: 2 号屏在 90 和 0 间切换
python rotate_screen.py portrait --device 2          :: 只操作 2 号屏
python rotate_screen.py --all                        :: 切换所有显示器的方向
python rotate_screen.py --list                       :: 列出所有显示器及当前状态
```

`快速切换.bat` 也支持加参数强制方向，优先于双角度切换：

```bat
快速切换.bat portrait    :: 强制竖屏
快速切换.bat 90          :: 旋转到 90 度
```

## 工作原理

1. 通过 `EnumDisplayDevicesW` 枚举所有连接到桌面的显示器；
2. 读取当前显示模式（`EnumDisplaySettingsW`），按目标方向交换宽高；
3. 枚举驱动支持的全部显示模式，挑选宽高互换、色深相同的候选（刷新率优先匹配）；
4. 依次尝试应用：`CDS_TEST` 预验证 + `CDS_UPDATEREGISTRY` 持久化 → `flags=0` 动态生效（可精确指定显示器）→ 旧 API `ChangeDisplaySettingsW` 回退；
5. 应用后对比所有屏幕的前后状态，确认变化确实发生在所选屏幕上，否则明确告警。

## 已知限制 / 故障排查

- **部分显卡驱动不支持旋转**：切换失败并提示"模式不受支持"时，请在 NVIDIA 控制面板 → 显示 → 旋转显示器 中确认允许旋转。
- **本机实测旋转会被系统自动恢复**（约几十秒到几分钟，疑似驱动/系统层面重置动态显示模式，程序无法阻止）；换机器通常正常。若发生，屏幕会自己弹回原方向，重新切换即可。
- **非主显示器只能临时旋转**：某些驱动对副屏只接受动态模式（见上一条）。
- **双击 bat 提示找不到 python**：需安装 Python 并加入 PATH（安装时勾选 "Add Python to PATH"）。
- **编辑器类型告警**：`pyrightconfig.json` 已屏蔽 ctypes 脚本固有的类型注解告警，不影响运行。

## 环境要求

- Windows（依赖 Win32 显示 API，不支持 Linux/macOS）
- Python 3.x（任意版本，标准库）
