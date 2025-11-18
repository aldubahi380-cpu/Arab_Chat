# سكريبت لتحميل gradle-wrapper.jar
Write-Host "Downloading gradle-wrapper.jar..." -ForegroundColor Yellow

$url = "https://github.com/gradle/gradle/raw/v8.2.0/gradle/wrapper/gradle-wrapper.jar"
$output = "gradle\wrapper\gradle-wrapper.jar"

try {
    # إنشاء المجلد إذا لم يكن موجوداً
    $dir = Split-Path -Parent $output
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    
    # تحميل الملف
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
    
    if (Test-Path $output) {
        $size = (Get-Item $output).Length
        Write-Host "✅ Success! Downloaded gradle-wrapper.jar ($size bytes)" -ForegroundColor Green
        Write-Host "Location: $output" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Download failed - file not found" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTry downloading manually:" -ForegroundColor Yellow
    Write-Host "1. Open browser and go to: $url" -ForegroundColor Cyan
    Write-Host "2. Save the file as: gradle-wrapper.jar" -ForegroundColor Cyan
    Write-Host "3. Place it in: gradle\wrapper\" -ForegroundColor Cyan
}

