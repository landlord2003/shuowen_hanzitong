@echo off
chcp 65001 >nul
rem ============================================================
rem  说文解字·汉字通 —— 本地预览服务（唯一启动入口）
rem  双击即用：启动多线程服务 → 2 秒后自动打开浏览器
rem
rem  为什么不直接用 python -m http.server：
rem    那是单线程服务，会被本应用的并发大请求压垮 ——
rem    index.html 13.8MB + dataset.bin 14.2MB + stroke_data.json 20.3MB
rem    同时拉取时偶发把大文件发成空体，导致字形演变图整片空白。
rem    serve_8941.py 用的是 ThreadingHTTPServer，可并发。
rem
rem  另注意：本应用不能直接双击 index.html 打开。
rem    字形演变图与笔顺依赖 fetch() 读取本地数据文件，
rem    file:// 协议下会被浏览器 CORS 拦截。
rem ============================================================

set "PORT=8941"
set "PYEXE="
set "PYARG="

rem 1) WorkBuddy 自带 Python（用 %USERPROFILE%，不写死用户名）
if exist "%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe" set "PYEXE=%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe" set "PYEXE=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"

rem 2) 系统 py 启动器
if not defined PYEXE (
  where py >nul 2>nul
  if not errorlevel 1 ( set "PYEXE=py" & set "PYARG=-3" )
)
rem 3) PATH 中的 python / python3
if not defined PYEXE ( where python >nul 2>nul && set "PYEXE=python" )
if not defined PYEXE ( where python3 >nul 2>nul && set "PYEXE=python3" )

if not defined PYEXE (
  echo [X] 未找到 Python，无法启动本地服务。
  echo     安装 Python 后重试；或在本目录手动执行：
  echo         python -m http.server %PORT%
  echo     但不要双击 index.html 直接打开（见本文件顶部说明）。
  pause
  exit /b 1
)

echo ============================================
echo   说文解字 Web App - 本地预览
echo   解释器: %PYEXE% %PYARG%
echo   服务  : %~dp0serve_8941.py
echo   地址  : http://127.0.0.1:%PORT%/index.html
echo   关闭本窗口即停止服务。
echo ============================================

start "" /min "%PYEXE%" %PYARG% "%~dp0serve_8941.py"
timeout /t 2 >nul
start "" "http://127.0.0.1:%PORT%/index.html"
