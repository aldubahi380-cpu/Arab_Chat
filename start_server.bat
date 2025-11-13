@echo off
chcp 65001 >nul
cd /d "%~dp0"
call my_env\Scripts\activate.bat

echo ============================================
echo 🌐 واتساب الدوبحي - تشغيل على الشبكة المحلية
echo ============================================

REM الحصول على عنوان IP المحلي
echo.
echo 📡 الحصول على عنوان IP المحلي...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo.
echo ============================================
echo 📍 معلومات الاتصال:
echo ============================================
echo الوصول المحلي:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo.
echo الوصول من الأجهزة الأخرى على نفس الشبكة:
echo   - http://%IP%:8000
echo ============================================
echo.
echo ⚠️  اضغط Ctrl+C لإيقاف السيرفر
echo.
pause

echo.
echo 🚀 تشغيل السيرفر...
echo.

python manage.py runserver 0.0.0.0:8000

pause

