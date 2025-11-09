@echo off
chcp 65001 >nul
cd /d "E:\A CHat"
call my_env\Scripts\activate.bat
echo ============================================
echo فحص المايجريشن...
echo ============================================
python manage.py showmigrations
echo.
echo ============================================
echo تطبيق المايجريشن...
echo ============================================
python manage.py migrate
echo.
echo ============================================
echo تم الانتهاء!
echo ============================================
pause

