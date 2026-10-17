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
:: 注意：必须用带引号的 set 形式，否则 cmd 会剥掉结尾空格，
:: 导致最后一个角度 270 永远无法通过校验
set "VALID= 0 90 180 270 "

:: ---------- 读取现有配置作为默认值 ----------
set SCREEN=1
set A1=90
set A2=0
if exist "%CFG%" (
    for /f "usebackq tokens=1,2,3 delims=|" %%a in ("%CFG%") do (
        set SCREEN=%%a
        set A1=%%b
        set A2=%%c
    )
) else if exist screen.cfg (
    set /p SCREEN=<screen.cfg
)

echo ============================================
echo   快速切换设置
echo   （设置后双击 快速切换.bat 即在两个角度间切换）
echo ============================================
echo.
python rotate_screen.py --list
echo.

:ask_screen
set /p NUM=请选择屏幕编号（回车=%SCREEN%）:
if "%NUM%"=="" set NUM=%SCREEN%
echo %NUM%| findstr /r "^[1-9][0-9]*$" >nul || (
    echo 请输入有效的屏幕编号
    goto ask_screen
)

:ask_a1
set /p IN1=角度1（回车=%A1%，可选 0/90/180/270）:
if "%IN1%"=="" set IN1=%A1%
echo %VALID%| findstr /c:" %IN1% " >nul || (
    echo 角度只能是 0 / 90 / 180 / 270
    goto ask_a1
)

:ask_a2
set /p IN2=角度2（回车=%A2%，可选 0/90/180/270）:
if "%IN2%"=="" set IN2=%A2%
echo %VALID%| findstr /c:" %IN2% " >nul || (
    echo 角度只能是 0 / 90 / 180 / 270
    goto ask_a2
)

:: 注意：重定向必须放在 echo 前面。若写成 echo ...%IN2%>"文件"，
:: 当角度以 0 结尾时 cmd 会把 "0>" 当成 stdin 重定向句柄，导致配置写不进文件
>"%CFG%" echo %NUM%^|%IN1%^|%IN2%

echo.
echo 已保存：
echo   屏幕编号 : %NUM%
echo   角度1    : %IN1%
echo   角度2    : %IN2%
echo.
echo 之后双击 快速切换.bat 即可在这两个角度间切换。
pause
