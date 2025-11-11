from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from chat.services.account_cleanup import delete_user_account

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "احذف كل المستخدمين وبياناتهم المرتبطة لتفريغ المساحة."

    def add_arguments(self, parser):
        parser.add_argument(
            "--include-superusers",
            action="store_true",
            default=False,
            help="حذف المدراء (superusers) أيضاً. بشكل افتراضي يتم الاحتفاظ بهم.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="عرض الأعداد فقط بدون تنفيذ الحذف.",
        )

    def handle(self, *args, **options):
        include_superusers: bool = options["include_superusers"]
        dry_run: bool = options["dry_run"]

        User = get_user_model()

        queryset = User.objects.all()
        if not include_superusers:
            queryset = queryset.filter(is_superuser=False)

        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("لا يوجد مستخدمون للحذف."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"سيتم حذف {total} مستخدم/مستخدمين وما يرتبط بهم من بيانات."
            )
        )

        if dry_run:
            self.stdout.write(self.style.NOTICE("وضع التجربة مفعّل، لم يتم تنفيذ أي حذف."))
            return

        with transaction.atomic():
            for user in queryset.iterator(chunk_size=50):
                logger.info("Deleting user %s (id=%s)", user.username, user.pk)
                delete_user_account(user.id)

        self.stdout.write(self.style.SUCCESS(f"تم حذف {total} مستخدم/مستخدمين بنجاح."))

