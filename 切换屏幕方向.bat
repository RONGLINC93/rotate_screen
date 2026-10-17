@echo off
chcp 65001 >nul
cd /d %~dp0
echo ================================
echo   屏幕横竖屏切换工具
echo   （在菜单中选择屏幕编号和操作）
echo ================================
echo.
python rotate_screen.py
pause
