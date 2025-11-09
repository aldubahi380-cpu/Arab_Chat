@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM إيقاف أي عملية على المنفذ 8000
echo.
echo ============================================
echo 🔍 فحص وإيقاف العمليات على المنفذ 8000...
echo ============================================
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo إيقاف العملية %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ============================================
echo 🚀 تشغيل السيرفر على الشبكة المحلية...
echo ============================================
echo.

REM الحصول على IP المحلي
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo.
echo 📍 معلومات الاتصال:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo   - http://%IP%:8000
echo.
echo ============================================
echo.

call my_env\Scripts\activate.bat
python manage.py runserver 0.0.0.0:8000

