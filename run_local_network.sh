#!/bin/bash

echo "============================================"
echo "تشغيل سيرفر عرب شات على الشبكة المحلية"
echo "============================================"
echo ""

cd "$(dirname "$0")"
source my_env/bin/activate

# الحصول على عنوان IP المحلي
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "عنوان IP المحلي: $LOCAL_IP"
echo ""
echo "============================================"
echo "السيرفر سيعمل على:"
echo "- http://localhost:8000"
echo "- http://127.0.0.1:8000"
echo "- http://$LOCAL_IP:8000"
echo "============================================"
echo ""
echo "يمكن للأجهزة الأخرى على نفس الشبكة الوصول عبر:"
echo "http://$LOCAL_IP:8000"
echo ""
echo "اضغط Ctrl+C لإيقاف السيرفر"
echo ""

python manage.py runserver 0.0.0.0:8000

