"""
سكريبت لإنشاء مستخدم الإدارة
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arab_chat.settings')
django.setup()

from django.contrib.auth.models import User

# إنشاء مستخدم الإدارة
username = 'ahmed'
password = '123'
email = 'ahmed@arabchat.com'

if User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f'تم تحديث مستخدم الإدارة: {username}')
else:
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f'تم إنشاء مستخدم الإدارة: {username}')

print(f'اسم المستخدم: {username}')
print(f'كلمة المرور: {password}')
print('يمكنك الآن تسجيل الدخول إلى لوحة الإدارة على: http://localhost:8000/admin/')

