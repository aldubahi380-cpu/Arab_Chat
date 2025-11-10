from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0014_message_is_edited'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='covers/', verbose_name='صورة الغلاف'),
        ),
    ]
