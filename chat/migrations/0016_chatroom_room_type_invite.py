from django.db import migrations, models
import secrets


def populate_room_meta(apps, schema_editor):
    ChatRoom = apps.get_model('chat', 'ChatRoom')
    for room in ChatRoom.objects.all():
        if not room.room_type:
            room.room_type = 'community'
        if room.room_type == 'group':
            room.is_private = True
            if not room.invite_code:
                room.invite_code = secrets.token_urlsafe(8).replace('-', '').replace('_', '')[:10]
        else:
            room.is_private = False
            room.invite_code = None
        room.save(update_fields=['room_type', 'is_private', 'invite_code'])


def reverse_room_meta(apps, schema_editor):
    ChatRoom = apps.get_model('chat', 'ChatRoom')
    ChatRoom.objects.update(room_type='community', invite_code=None, is_private=False)


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0015_userprofile_cover_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='invite_code',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True, verbose_name='رمز الدعوة'),
        ),
        migrations.AddField(
            model_name='chatroom',
            name='room_type',
            field=models.CharField(choices=[('community', 'مجتمع'), ('group', 'مجموعة')], default='community', max_length=20, verbose_name='نوع الغرفة'),
        ),
        migrations.RunPython(populate_room_meta, reverse_room_meta),
    ]
