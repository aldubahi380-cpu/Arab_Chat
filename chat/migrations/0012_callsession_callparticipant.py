from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_message_original_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CallSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('call_type', models.CharField(choices=[('audio', 'صوتية'), ('video', 'فيديو')], default='audio', max_length=10, verbose_name='نوع المكالمة')),
                ('status', models.CharField(choices=[('pending', 'قيد الإنشاء'), ('active', 'نشطة'), ('ended', 'منتهية'), ('cancelled', 'ملغاة')], default='pending', max_length=10, verbose_name='الحالة')),
                ('end_reason', models.CharField(blank=True, choices=[('normal', 'انتهت بشكل طبيعي'), ('cancelled', 'ألغيت من أحد الأطراف'), ('timeout', 'انتهت لانتهاء الوقت'), ('no_participants', 'انتهت لانقطاع الجميع')], max_length=20, null=True, verbose_name='سبب الانتهاء')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ بدء المكالمة')),
                ('ended_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ انتهاء المكالمة')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')),
                ('initiator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='initiated_calls', to=settings.AUTH_USER_MODEL, verbose_name='المنشئ')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='call_sessions', to='chat.chatroom', verbose_name='غرفة الدردشة')),
            ],
            options={
                'verbose_name': 'جلسة مكالمة',
                'verbose_name_plural': 'جلسات المكالمات',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['status', '-created_at'], name='chat_calls_status_created_idx'),
                    models.Index(fields=['room', 'status'], name='chat_calls_room_status_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='CallParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('caller', 'المتصل'), ('receiver', 'المستقبل')], default='receiver', max_length=10, verbose_name='الدور')),
                ('peer_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='معرف الPeer')),
                ('is_connected', models.BooleanField(default=False, verbose_name='متصل حالياً')),
                ('joined_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الانضمام')),
                ('left_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ المغادرة')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='chat.callsession', verbose_name='جلسة المكالمة')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='call_participations', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'مشارك في المكالمة',
                'verbose_name_plural': 'مشاركو المكالمات',
                'indexes': [
                    models.Index(fields=['session', 'user'], name='chat_call_session_user_idx'),
                    models.Index(fields=['user', 'is_connected'], name='chat_call_user_connected_idx'),
                ],
                'unique_together': {('session', 'user')},
            },
        ),
    ]

