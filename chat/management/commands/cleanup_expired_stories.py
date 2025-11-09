from django.core.management.base import BaseCommand

from chat.models import Story


class Command(BaseCommand):
    help = 'يحذف الاستوريات المنتهية (أقدم من 24 ساعة) ويزيل الملفات المرتبطة بها.'

    def handle(self, *args, **options):
        deleted_count = Story.objects.purge_expired()
        self.stdout.write(self.style.SUCCESS(f'تم حذف {deleted_count} استوري منتهٍ.'))

