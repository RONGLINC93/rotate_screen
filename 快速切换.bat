@echo off
chcp 65001 >nul
cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 python，请先安装 Python 并加入 PATH
    pause
    exit /b 1
)

set CFG=quickswitch.cfg

if not exist "%CFG%" (
    echo 尚未设置。请先运行 快速切换设置.bat 选择屏幕和切换角度。
    pause
    exit /b 1
)

for /f "usebackq tokens=1,2,3 delims=|" %%a in ("%CFG%") do (
    set SCREEN=%%a
    set A1=%%b
    set A2=%%c
)

if "%SCREEN%"=="" (
    echo 配置文件损坏，请运行 快速切换设置.bat 重新设置。
    pause
    exit /b 1
)
if "%A1%"=="" (
    echo 配置中缺少角度1，请运行 快速切换设置.bat 重新设置。
    pause
    exit /b 1
)
if "%A2%"=="" (
    echo 配置中缺少角度2，请运行 快速切换设置.bat 重新设置。
    pause
    exit /b 1
)

:: ---------- 执行切换（可加参数 portrait / landscape / 90 等，优先于双角度） ----------
python rotate_screen.py %1 --angles %A1%,%A2% --device %SCREEN%

