@echo off
chcp 65001 >nul
echo ============================================================
echo   真机网络可达性测试（B 路线数据源）
echo   双击运行即可，测试你的网络能否直连海外字形图源
echo ============================================================
echo.

echo [1/4] 测试 GlyphWiki（A 路线，对照组，应该能通）
curl -sS --max-time 15 -o nul -w "  结果: HTTP %%{http_code}  用时 %%{time_total}s" "https://glyphwiki.org/glyph/u4e00.svg"
echo.
echo.

echo [2/4] 测试 Wikimedia Commons API（B 路线小篆）
curl -sS --max-time 15 -o nul -w "  结果: HTTP %%{http_code}  用时 %%{time_total}s" "https://commons.wikimedia.org/w/api.php?action=query&format=json"
echo.
echo.

echo [3/4] 测试 upload.wikimedia.org（B 路线图片直链）
curl -sS --max-time 15 -o nul -w "  结果: HTTP %%{http_code}  用时 %%{time_total}s" "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Seal_script_%%28regular%%29.svg/64px-Seal_script_%%28regular%%29.svg.png"
echo.
echo.

echo [4/4] 测试 Internet Archive（B 路线公版书影）
curl -sS --max-time 15 -o nul -w "  结果: HTTP %%{http_code}  用时 %%{time_total}s" "https://archive.org"
echo.
echo.

echo ============================================================
echo   判读方法：
echo   - HTTP 200 = 该源可达，可以在本机跑
echo   - HTTP 000 / 超时 = 该源被墙，需要海外伙伴
echo ============================================================
pause
