from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_sessiondevice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_type',
            field=models.CharField(
                choices=[
                    ('text', 'نص'),
                    ('image', 'صورة'),
                    ('video', 'فيديو'),
                    ('file', 'ملف'),
                    ('audio', 'صوت'),
                ],
                default='text',
                max_length=20,
                verbose_name='نوع الرسالة'
            ),
        ),
    ]
