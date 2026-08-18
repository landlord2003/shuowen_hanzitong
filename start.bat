@echo off
cd /d "%~dp0"
echo ============================================
echo  ShuoWenJieZi - local glyph server
echo  URL: http://127.0.0.1:8765/index.html
echo  (browser will open automatically)
echo  Press Ctrl+C to stop the server
echo ============================================
start "" "http://127.0.0.1:8765/index.html"
python -m http.server 8765 --bind 127.0.0.1
