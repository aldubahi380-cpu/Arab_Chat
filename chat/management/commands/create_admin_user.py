from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'إنشاء مستخدم الإدارة'

    def handle(self, *args, **options):
        username = 'ahmed'
        password = '123'
        email = 'ahmed@arabchat.com'

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'تم تحديث مستخدم الإدارة: {username}'))
        else:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'تم إنشاء مستخدم الإدارة: {username}'))

        self.stdout.write(self.style.SUCCESS(f'اسم المستخدم: {username}'))
        self.stdout.write(self.style.SUCCESS(f'كلمة المرور: {password}'))
        self.stdout.write(self.style.SUCCESS('يمكنك الآن تسجيل الدخول إلى لوحة الإدارة'))

