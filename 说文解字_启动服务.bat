@echo off
rem 说文解字·汉字通 —— 本地预览服务启动器
rem 双击即用：先起多线程预览服务(8941)，2秒后自动开浏览器
set "PYTHON_EXE=python"
if exist "C:\Users\Lenovo\.workbuddy\binaries\python\versions\3.13.12\python.exe" (set "PYTHON_EXE=C:\Users\Lenovo\.workbuddy\binaries\python\versions\3.13.12\python.exe")
start "" /min "%PYTHON_EXE%" "%~dp0serve_8941.py"
timeout /t 2 >nul
start "" "http://127.0.0.1:8941/index.html"
