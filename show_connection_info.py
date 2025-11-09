#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

ip = get_local_ip()

print("\n" + "=" * 60)
print("السيرفر يعمل على الشبكة المحلية!")
print("=" * 60)
print("\nالوصول المحلي:")
print("   - http://localhost:8000")
print("   - http://127.0.0.1:8000")
print("\nالوصول من الاجهزة الاخرى على نفس الشبكة:")
print(f"   - http://{ip}:8000")
print("\nAPI Endpoints:")
print(f"   - http://{ip}:8000/api/")
print(f"   - http://{ip}:8000/api/users/")
print(f"   - http://{ip}:8000/api/otp/send_otp/")
print(f"   - http://{ip}:8000/api/otp/verify_otp/")
print("\n" + "=" * 60)
print("ملاحظات:")
print("   1. تاكد من ان جميع الاجهزة على نفس الشبكة WiFi")
print("   2. تاكد من ان الجدار الناري يسمح بالاتصال عبر المنفذ 8000")
print("   3. اضغط Ctrl+C في نافذة السيرفر لايقافه")
print("=" * 60 + "\n")

