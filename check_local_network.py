#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script للتحقق من إعدادات الشبكة المحلية
"""
import socket
import sys
import os

def get_local_ip():
    """الحصول على عنوان IP المحلي"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return None

def check_port(port=8000):
    """التحقق من أن المنفذ متاح"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0  # True إذا كان المنفذ مستخدم
    except Exception:
        return False

def check_django_settings():
    """التحقق من إعدادات Django"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arab_chat.settings')
        import django
        django.setup()
        
        from django.conf import settings
        
        print("=" * 60)
        print("✅ إعدادات Django:")
        print("=" * 60)
        print(f"DEBUG: {settings.DEBUG}")
        print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # التحقق من LOCAL_IP
        if hasattr(settings, 'LOCAL_IP'):
            print(f"LOCAL_IP: {settings.LOCAL_IP}")
        
        # التحقق من CORS
        if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS'):
            print(f"CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
        
        print("=" * 60)
        return True
    except Exception as e:
        print(f"❌ خطأ في فحص إعدادات Django: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 فحص إعدادات الشبكة المحلية - عرب شات")
    print("=" * 60)
    print()
    
    # 1. الحصول على IP المحلي
    print("1️⃣  الحصول على عنوان IP المحلي...")
    local_ip = get_local_ip()
    if local_ip:
        print(f"   ✅ IP المحلي: {local_ip}")
    else:
        print("   ❌ فشل الحصول على IP المحلي")
        return
    
    print()
    
    # 2. التحقق من المنفذ
    print("2️⃣  التحقق من المنفذ 8000...")
    port_in_use = check_port(8000)
    if port_in_use:
        print("   ⚠️  المنفذ 8000 مستخدم (السيرفر قد يكون يعمل)")
    else:
        print("   ✅ المنفذ 8000 متاح")
    
    print()
    
    # 3. التحقق من إعدادات Django
    print("3️⃣  فحص إعدادات Django...")
    django_ok = check_django_settings()
    
    print()
    print("=" * 60)
    print("📋 ملخص:")
    print("=" * 60)
    print(f"IP المحلي: {local_ip}")
    print(f"الوصول المحلي: http://localhost:8000")
    print(f"الوصول من الشبكة: http://{local_ip}:8000")
    print()
    
    if django_ok:
        print("✅ جميع الفحوصات نجحت!")
        print()
        print("🚀 لتشغيل السيرفر:")
        print("   python manage.py runserver 0.0.0.0:8000")
        print("   أو استخدم: run_local_network.bat")
    else:
        print("⚠️  يرجى التحقق من إعدادات Django")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

