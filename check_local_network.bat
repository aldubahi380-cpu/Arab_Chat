@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo 🔍 فحص إعدادات الشبكة المحلية - عرب شات
echo ============================================
echo.

REM الحصول على عنوان IP المحلي
echo 📡 الحصول على عنوان IP المحلي...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo.
echo ============================================
echo ✅ معلومات الشبكة:
echo ============================================
echo IP المحلي: %IP%
echo.
echo ============================================
echo 📋 روابط الوصول:
echo ============================================
echo الوصول المحلي:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo.
echo الوصول من الأجهزة الأخرى:
echo   - http://%IP%:8000
echo.
echo API Endpoints:
echo   - http://%IP%:8000/api/
echo   - http://%IP%:8000/api/users/
echo   - http://%IP%:8000/api/otp/send_otp/
echo ============================================
echo.

REM فحص إعدادات Django
echo 🔍 فحص إعدادات Django...
call my_env\Scripts\activate.bat
python check_local_network.py

echo.
echo ============================================
echo ✅ انتهى الفحص
echo ============================================
echo.
pause

