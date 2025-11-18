# سكريبت لتحديث API URL في build.gradle
param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl
)

$buildGradle = "app\build.gradle"

if (-not (Test-Path $buildGradle)) {
    Write-Host "❌ File not found: $buildGradle" -ForegroundColor Red
    exit 1
}

# تنظيف URL (إزالة https:// و / في النهاية)
$cleanUrl = $ServerUrl -replace '^https?://', '' -replace '/$', ''

Write-Host "Updating API URL to: https://$cleanUrl" -ForegroundColor Yellow

# قراءة الملف
$content = Get-Content $buildGradle -Raw

# تحديث API_BASE_URL و WS_BASE_URL في جميع الأماكن
$content = $content -replace 'buildConfigField "String", "API_BASE_URL", ''"https://your-app\.onrender\.com/api"''', "buildConfigField `"String`", `"API_BASE_URL`", `"`"https://$cleanUrl/api`"`""
$content = $content -replace 'buildConfigField "String", "WS_BASE_URL", ''"wss://your-app\.onrender\.com/ws"''', "buildConfigField `"String`", `"WS_BASE_URL`", `"`"wss://$cleanUrl/ws`"`""

# كتابة الملف
Set-Content -Path $buildGradle -Value $content -NoNewline

Write-Host "✅ Updated build.gradle successfully!" -ForegroundColor Green
Write-Host "API URL: https://$cleanUrl/api" -ForegroundColor Cyan
Write-Host "WS URL: wss://$cleanUrl/ws" -ForegroundColor Cyan

