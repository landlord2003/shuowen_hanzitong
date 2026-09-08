# 真机网络可达性测试（B 路线数据源）
# 用法：右键 -> 使用 PowerShell 运行，或复制到 PowerShell 粘贴回车
$ErrorActionPreference = "SilentlyContinue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  真机网络可达性测试（B 路线数据源）" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$targets = @(
    @{ Name = "GlyphWiki (A路线·对照组)"; Url = "https://glyphwiki.org/glyph/u4e00.svg" },
    @{ Name = "Wikimedia Commons API (B·小篆)"; Url = "https://commons.wikimedia.org/w/api.php?action=query&format=json" },
    @{ Name = "upload.wikimedia.org (B·图片直链)"; Url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Seal_script_%28regular%29.svg/64px-Seal_script_%28regular%29.svg.png" },
    @{ Name = "Internet Archive (B·公版书影)"; Url = "https://archive.org" }
)

$i = 0
foreach ($t in $targets) {
    $i++
    Write-Host "[$i/4] 测试 $($t.Name)" -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-WebRequest -Uri $t.Url -TimeoutSec 15 -UseBasicParsing
        $sw.Stop()
        Write-Host "      HTTP $($resp.StatusCode)  ·  用时 $([math]::Round($sw.Elapsed.TotalSeconds,2))s" -ForegroundColor Green
    } catch {
        $sw.Stop()
        $code = $_.Exception.Response.StatusCode.value__
        if ($code) {
            Write-Host "      HTTP $code  ·  用时 $([math]::Round($sw.Elapsed.TotalSeconds,2))s" -ForegroundColor Red
        } else {
            Write-Host "      超时/连接失败  ·  $([math]::Round($sw.Elapsed.TotalSeconds,2))s  (可能被墙)" -ForegroundColor Red
        }
    }
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  判读：" -ForegroundColor Cyan
Write-Host "  · HTTP 200 (绿色)  = 该源可达，本机能跑" -ForegroundColor Green
Write-Host "  · 超时/失败 (红色) = 该源被墙，需海外伙伴" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键关闭..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
