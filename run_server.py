#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to check migrations and start Django server on local network
"""
import os
import sys
import subprocess
import socket

def get_local_ip():
    """الحصول على عنوان IP المحلي للشبكة"""
    try:
        # إنشاء socket للاتصال بخادم خارجي (لا يرسل بيانات فعلياً)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Activate virtual environment by setting Python path
    venv_python = os.path.join(project_dir, "my_env", "Scripts", "python.exe")
    
    # إذا لم يكن موجود، حاول مسارات أخرى
    if not os.path.exists(venv_python):
        venv_python = os.path.join(project_dir, "my_env", "bin", "python")
        if not os.path.exists(venv_python):
            print("❌ لم يتم العثور على البيئة الافتراضية!")
            print("❌ Virtual environment not found!")
            print(f"بحث في: {project_dir}")
            return
    
    # الحصول على IP المحلي
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("🌐 عرب شات - تشغيل على الشبكة المحلية")
    print("=" * 60)
    print(f"📁 المجلد: {project_dir}")
    print(f"🌐 IP المحلي: {local_ip}")
    print("=" * 60)
    
    print("\n🔍 فحص المايجريشن...")
    print("-" * 60)
    
    # Check migrations
    result = subprocess.run([venv_python, "manage.py", "showmigrations"], 
                          capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    print("\n🔄 تطبيق المايجريشن...")
    print("-" * 60)
    
    # Apply migrations
    result = subprocess.run([venv_python, "manage.py", "migrate"], 
                          capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    print("\n" + "=" * 60)
    print("🚀 تشغيل السيرفر على الشبكة المحلية...")
    print("=" * 60)
    print(f"📍 الوصول المحلي:")
    print(f"   - http://localhost:8000")
    print(f"   - http://127.0.0.1:8000")
    print(f"📍 الوصول من الأجهزة الأخرى على نفس الشبكة:")
    print(f"   - http://{local_ip}:8000")
    print("=" * 60)
    print("⚠️  اضغط Ctrl+C لإيقاف السيرفر")
    print("=" * 60)
    print()
    
    # Start server on all interfaces (0.0.0.0)
    subprocess.run([venv_python, "manage.py", "runserver", "0.0.0.0:8000"])

if __name__ == "__main__":
    main()


