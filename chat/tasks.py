from __future__ import annotations

from celery import shared_task
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from .services.account_cleanup import delete_user_account


@shared_task(bind=True, ignore_result=True, max_retries=3, default_retry_delay=30)
def send_message_notification_task(self, message_id: int, recipient_id: int) -> None:
    """
    إرسال إشعار Push عند استقبال رسالة جديدة (يعمل في الخلفية عبر Celery).
    """
    from .models import Message  # استيراد متأخر لتجنب الدوران
    from .push_notifications_service import push_notification_service

    try:
        message = Message.objects.select_related('room', 'sender').get(id=message_id)
    except Message.DoesNotExist as exc:
        raise self.retry(exc=exc, countdown=10, max_retries=2)

    User = get_user_model()
    try:
        recipient = User.objects.get(id=recipient_id, is_active=True)
    except User.DoesNotExist:
        return

    # تجنب إرسال إشعارات للمستخدمين المتصلين حديثاً إذا لم تمض دقيقة واحدة
    profile = getattr(recipient, 'profile', None)
    if profile and profile.is_online and profile.last_seen and (timezone.now() - profile.last_seen).total_seconds() < 30:
        return

    push_notification_service.send_message_notification(message, recipient)


@shared_task(bind=True, ignore_result=True, max_retries=3, default_retry_delay=15)
def send_call_invite_task(self, call_session_id: int, recipient_id: int) -> None:
    """
    إرسال إشعار دعوة مكالمة (صوتية/فيديو) عبر FCM.
    """
    from .models import CallSession  # استيراد متأخر لتجنب الدوران
    from .push_notifications_service import push_notification_service

    try:
        call_session = (
            CallSession.objects.select_related('room', 'initiator')
            .prefetch_related('participants__user')
            .get(id=call_session_id)
        )
    except CallSession.DoesNotExist as exc:
        raise self.retry(exc=exc, countdown=10, max_retries=2)

    if call_session.status != CallSession.Status.ACTIVE:
        return

    User = get_user_model()
    try:
        recipient = User.objects.get(id=recipient_id, is_active=True)
    except User.DoesNotExist:
        return

    push_notification_service.send_call_invitation(call_session, recipient)


@shared_task(bind=True, ignore_result=True, max_retries=3, default_retry_delay=60)
def send_story_notification_task(self, story_id: int, recipient_id: int) -> None:
    """
    إرسال إشعار عند نشر استوري جديد.
    """
    from .models import Story  # استيراد متأخر لتجنب الدوران
    from .push_notifications_service import push_notification_service

    try:
        story = Story.objects.select_related('user').get(id=story_id)
    except Story.DoesNotExist:
        return

    if not story.is_active:
        return

    User = get_user_model()
    try:
        recipient = User.objects.get(id=recipient_id, is_active=True)
    except User.DoesNotExist:
        return

    # لا داعي لإرسال إشعار للمالك نفسه عبر هذا المسار
    if recipient.id == story.user_id:
        return

    push_notification_service.send_story_notification(story, recipient)


@shared_task(bind=True, ignore_result=True, max_retries=2, default_retry_delay=60)
def cleanup_stale_call_sessions(self) -> None:
    """
    إنهاء المكالمات التي تجاوزت المدة المسموح بها أو التي انقطع جميع المشاركين فيها.
    """
    from .models import CallSession, CallParticipant

    max_age_minutes = getattr(settings, 'CALL_SESSION_MAX_MINUTES', 120) or 120
    cutoff = timezone.now() - timedelta(minutes=max_age_minutes)

    stale_sessions = CallSession.objects.filter(
        status=CallSession.Status.ACTIVE,
        created_at__lt=cutoff,
    )
    ended_count = 0
    for session in stale_sessions:
        session.end(reason=CallSession.EndReason.TIMEOUT)
        ended_count += 1

    # التعامل مع المكالمات التي لا تحتوي على مشاركين متصلين
    empty_sessions = CallSession.objects.filter(
        status=CallSession.Status.ACTIVE,
        participants__is_connected=False,
    ).annotate(
        connected_count=Count(
            'participants',
            filter=Q(participants__is_connected=True)
        )
    ).filter(connected_count=0)
    for session in empty_sessions:
        session.end(reason=CallSession.EndReason.NO_PARTICIPANTS)
        ended_count += 1

    return ended_count


@shared_task(bind=True, ignore_result=True)
def cleanup_stale_session_devices(self) -> None:
    """
    تعطيل الأجهزة المنتهية صلاحيتها.
    """
    from .models import SessionDevice

    now = timezone.now()
    expired_devices = SessionDevice.objects.filter(is_active=True, expires_at__lt=now)
    for device in expired_devices:
        device.is_active = False
        device.save(update_fields=['is_active'])
    return expired_devices.count()


@shared_task(bind=True, ignore_result=True)
def cleanup_expired_otps(self) -> None:
    """
    حذف رموز OTP المنتهية الصلاحية.
    """
    from .models import OTPVerification

    OTPVerification.objects.filter(expires_at__lt=timezone.now()).delete()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
    ignore_result=True,
)
def delete_user_account_task(self, user_id: int) -> None:
    """
    حذف حساب مستخدم وجميع البيانات المرتبطة به في الخلفية.
    """
    delete_user_account(user_id)

