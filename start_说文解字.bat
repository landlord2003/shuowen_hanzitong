@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   说文解字 Web App —— 本地一键预览
echo ============================================
echo   浏览器将自动打开: http://127.0.0.1:8080/index.html
echo   关闭本窗口即停止服务。
echo.
echo   [重要] 当前磁盘文件可能是旧版（扩容前的字形）。
echo   要看最新「甲骨文/金文/大篆扩量 + 隶书补全」效果，
echo   请先在本目录执行一次同步（需已 push 或已 pull）：
echo       git fetch
echo       git reset --hard main
echo   然后再双击本启动器。
echo ============================================
echo.
start "" "http://127.0.0.1:8080/index.html"
python -m http.server 8080
if errorlevel 1 (
  echo.
  echo [!] 未找到 python 命令，尝试 python3 ...
  python3 -m http.server 8080
)
