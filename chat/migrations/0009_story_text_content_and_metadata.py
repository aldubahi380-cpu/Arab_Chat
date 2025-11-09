from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_alter_message_message_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='content',
            field=models.FileField(blank=True, null=True, upload_to='stories/', verbose_name='المحتوى'),
        ),
        migrations.AlterField(
            model_name='story',
            name='content_type',
            field=models.CharField(choices=[('image', 'صورة'), ('video', 'فيديو'), ('text', 'نص')], default='image', max_length=10, verbose_name='نوع المحتوى'),
        ),
        migrations.AddField(
            model_name='story',
            name='background_color',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='لون الخلفية'),
        ),
        migrations.AddField(
            model_name='story',
            name='font_color',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='لون الخط'),
        ),
        migrations.AddField(
            model_name='story',
            name='text_content',
            field=models.TextField(blank=True, null=True, verbose_name='المحتوى النصي'),
        ),
        migrations.AddField(
            model_name='story',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now, verbose_name='تاريخ التحديث'),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='story',
            index=models.Index(fields=['user', '-created_at'], name='chat_story_user_id_c25efb_idx'),
        ),
        migrations.AddIndex(
            model_name='story',
            index=models.Index(fields=['expires_at'], name='chat_story_expires_4f361b_idx'),
        ),
    ]

