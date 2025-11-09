from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_message_deleted_at_message_is_deleted'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='SessionDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_token', models.CharField(max_length=128, unique=True, verbose_name='رمز الجلسة')),
                ('device_id', models.CharField(max_length=128, unique=True, verbose_name='معرف الجهاز')),
                ('device_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='اسم الجهاز')),
                ('platform', models.CharField(blank=True, max_length=50, null=True, verbose_name='نظام التشغيل')),
                ('user_agent', models.CharField(blank=True, max_length=512, null=True, verbose_name='معلومات المتصفح')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='عنوان IP')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('expires_at', models.DateTimeField(verbose_name='تاريخ انتهاء الصلاحية')),
                ('last_seen', models.DateTimeField(auto_now=True, verbose_name='آخر استخدام')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_devices', to='auth.user', verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'جلسة جهاز',
                'verbose_name_plural': 'جلسات الأجهزة',
                'ordering': ['-last_seen'],
            },
        ),
        migrations.AddIndex(
            model_name='sessiondevice',
            index=models.Index(fields=['user', 'is_active'], name='chat_sessio_user_id_b29bd7_idx'),
        ),
        migrations.AddIndex(
            model_name='sessiondevice',
            index=models.Index(fields=['session_token'], name='chat_sessio_session_cb885f_idx'),
        ),
        migrations.AddIndex(
            model_name='sessiondevice',
            index=models.Index(fields=['device_id'], name='chat_sessio_device__43f410_idx'),
        ),
    ]


