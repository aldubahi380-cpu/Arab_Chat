from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0013_rename_chat_call_session_user_idx_chat_callpa_session_dc20e8_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='edited_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='تاريخ التعديل'),
        ),
        migrations.AddField(
            model_name='message',
            name='is_edited',
            field=models.BooleanField(default=False, verbose_name='تم التعديل'),
        ),
    ]
