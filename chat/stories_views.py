"""Views مطورة لميزة الاستوريات."""
import logging
from collections import OrderedDict
from datetime import timedelta
from pathlib import Path

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .media_utils import (
    compress_image,
    compress_video,
    ImageCompressionConfig,
    VideoCompressionConfig,
    IMAGE_CONFIG,
    VIDEO_CONFIG,
)
from .models import Friend, Story, StoryView
from .serializers import StorySerializer, StoryViewSerializer

logger = logging.getLogger(__name__)


def build_channels_context_for_user(user):
    """
    إرجاع بيانات أولية (placeholder) للقنوات المرتبطة بالمستخدم.
    يمكن استبدال المحتوى لاحقاً بنقاط بيانات حقيقية أو ربط مع API خارجي.
    """
    now = timezone.now()

    following = [
        {
            'id': 'tech-today',
            'name': 'تِك اليوم',
            'description': 'ملخّص يومي لأهم أخبار التقنية والابتكارات.',
            'followers': 18420,
            'is_verified': True,
            'is_muted': False,
            'cover_image': None,
            'last_post_at': now - timedelta(hours=3),
            'unread_posts': 4,
            'category': 'technology',
            'language': 'ar',
        },
        {
            'id': 'finance-digest',
            'name': 'ملخص المال',
            'description': 'تحليلات سريعة لأسواق المال والاقتصاد.',
            'followers': 11290,
            'is_verified': False,
            'is_muted': False,
            'cover_image': None,
            'last_post_at': now - timedelta(hours=8),
            'unread_posts': 0,
            'category': 'business',
            'language': 'ar',
        },
        {
            'id': 'gaming-now',
            'name': 'Gaming Now',
            'description': 'تغطية لأحدث ألعاب الفيديو والتحديثات الأسبوعية.',
            'followers': 9320,
            'is_verified': False,
            'is_muted': True,
            'cover_image': None,
            'last_post_at': now - timedelta(days=1, hours=2),
            'unread_posts': 1,
            'category': 'gaming',
            'language': 'ar',
        },
    ]

    suggested = [
        {
            'id': 'productivity-hacks',
            'name': 'Productivity Hacks',
            'description': 'نصائح قصيرة لرفع الإنتاجية وتنظيم الوقت.',
            'followers': 15670,
            'is_verified': True,
            'cover_image': None,
            'last_post_at': now - timedelta(hours=5),
            'trend_score': 87,
            'category': 'lifestyle',
            'language': 'en',
        },
        {
            'id': 'health-minute',
            'name': 'الصحة بالدقيقة',
            'description': 'معلومات سريعة حول العافية والصحة اليومية.',
            'followers': 20510,
            'is_verified': False,
            'cover_image': None,
            'last_post_at': now - timedelta(hours=12),
            'trend_score': 74,
            'category': 'health',
            'language': 'ar',
        },
        {
            'id': 'football-zone',
            'name': 'منطقة الكرة',
            'description': 'أبرز الأخبار والتحليلات عن كرة القدم العالمية.',
            'followers': 48900,
            'is_verified': True,
            'cover_image': None,
            'last_post_at': now - timedelta(hours=1, minutes=20),
            'trend_score': 93,
            'category': 'sports',
            'language': 'ar',
        },
    ]

    badge_count = sum(1 for channel in following if channel.get('unread_posts', 0) > 0)

    return {
        'following': following,
        'suggested': suggested,
        'badge_count': badge_count,
    }


class StoryViewSet(viewsets.ModelViewSet):
    """ViewSet للاستوريات بآلية مشابهة لواتساب"""

    MAX_VIDEO_SECONDS = getattr(settings, 'STORIES_MAX_VIDEO_SECONDS', 30)
    TARGET_VIDEO_WIDTH = getattr(settings, 'STORIES_TARGET_VIDEO_WIDTH', 720)
    TARGET_VIDEO_BITRATE = getattr(settings, 'STORIES_TARGET_VIDEO_BITRATE', '1200k')
    TARGET_IMAGE_MAX_EDGE = getattr(settings, 'STORIES_TARGET_IMAGE_MAX_EDGE', 1440)
    IMAGE_QUALITY = getattr(settings, 'STORIES_IMAGE_QUALITY', 88)

    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """عرض الاستوريات النشطة فقط"""
        Story.objects.purge_expired()
        return Story.objects.active().select_related('user', 'user__profile').prefetch_related('views')

    def get_serializer_context(self):
        """إضافة request والبيانات الإضافية إلى الـ context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """إنشاء استوري جديد (ينتهي بعد 24 ساعة)"""
        Story.objects.purge_expired()
        expires_at = timezone.now() + timedelta(hours=24)

        content_type = serializer.validated_data.get('content_type')
        extra_fields = {}
        if content_type == 'text':
            extra_fields['background_color'] = serializer.validated_data.get('background_color') or '#25D366'
            extra_fields['font_color'] = serializer.validated_data.get('font_color') or '#ffffff'

        story = serializer.save(
            user=self.request.user,
            expires_at=expires_at,
            **extra_fields,
        )

        try:
            self._post_process_story_media(story)
        except serializers.ValidationError:
            story.delete()
            raise
        except Exception as exc:
            logger.exception("Failed to optimise story media %s", story.id)
            story.delete()
            raise serializers.ValidationError({'content': 'تعذر معالجة الاستوري. يرجى المحاولة مرة أخرى.'}) from exc

        self._broadcast_story_update(story)

        # إرسال إشعارات Push للأصدقاء عبر Celery
        try:
            from .tasks import send_story_notification_task

            watcher_ids = Friend.objects.filter(friend=story.user).values_list('user_id', flat=True)
            for user_id in watcher_ids:
                send_story_notification_task.delay(story.id, user_id)
        except Exception as exc:
            logger.warning('Failed to enqueue story notifications: %s', exc)

    @action(detail=False, methods=['get'])
    def feed(self, request):
        """إرجاع الاستوريات مجمعة لواجهة واتساب"""
        Story.objects.purge_expired()
        now = timezone.now()
        user = request.user

        my_stories_qs = Story.objects.active().filter(user=user).order_by('created_at')
        friend_ids = Friend.objects.filter(user=user).values_list('friend_id', flat=True)
        friend_stories_qs = Story.objects.active().filter(
            user__in=friend_ids
        ).select_related('user', 'user__profile').order_by('user__id', 'created_at')

        viewed_story_ids = set(
            StoryView.objects.filter(
                user=user,
                story__expires_at__gt=now
            ).values_list('story_id', flat=True)
        )

        base_context = {**self.get_serializer_context(), 'viewed_story_ids': viewed_story_ids}
        my_stories_data = StorySerializer(my_stories_qs, many=True, context=base_context).data

        my_story_section = {
            'user': {
                'id': user.id,
                'username': user.username,
                'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None,
            },
            'stories': my_stories_data,
            'has_active': bool(my_stories_data),
            'last_story_at': my_stories_data[-1]['created_at'] if my_stories_data else None,
        }

        friend_stories_list = list(friend_stories_qs)
        serialized_friend_stories = StorySerializer(friend_stories_list, many=True, context=base_context).data

        grouped = OrderedDict()
        for story_obj, story_data in zip(friend_stories_list, serialized_friend_stories):
            friend_id = story_obj.user_id
            entry = grouped.get(friend_id)
            if entry is None:
                entry = {
                    'user': story_data['user'],
                    'stories': [],
                    'unseen_count': 0,
                    'last_story_at': story_data['created_at'],
                }
                grouped[friend_id] = entry

            entry['stories'].append(story_data)
            if story_data['id'] not in viewed_story_ids:
                entry['unseen_count'] += 1

            if story_data['created_at'] > entry['last_story_at']:
                entry['last_story_at'] = story_data['created_at']

        friends_feed = sorted(
            [
                {
                    **entry,
                    'has_unseen': entry['unseen_count'] > 0,
                }
                for entry in grouped.values()
            ],
            key=lambda item: item['last_story_at'],
            reverse=True,
        )

        badge_count = sum(1 for entry in friends_feed if entry['has_unseen'])

        channels_context = build_channels_context_for_user(user)

        return Response({
            'my_story': my_story_section,
            'friends': friends_feed,
            'badge_count': badge_count,
            'channels': {
                'following': channels_context['following'],
                'suggested': channels_context['suggested'],
            },
            'channel_badge_count': channels_context['badge_count'],
        })

    @action(detail=False, methods=['get'])
    def my_stories(self, request):
        """استورياتي النشطة"""
        stories = self.get_queryset().filter(user=request.user).order_by('created_at')
        context = {**self.get_serializer_context(), 'viewed_story_ids': set()}
        serializer = self.get_serializer(stories, many=True, context=context)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def friends_stories(self, request):
        """استوريات الأصدقاء - لأغراض التوافق"""
        feed_data = self.feed(request).data
        return Response(feed_data.get('friends', []))

    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """تسجيل مشاهدة استوري"""
        story = self.get_object()

        if story.expires_at < timezone.now():
            return Response(
                {'error': 'انتهت صلاحية هذا الاستوري'},
                status=status.HTTP_400_BAD_REQUEST
            )

        view_obj, created = StoryView.objects.get_or_create(
            story=story,
            user=request.user
        )

        if created:
            story.views_count = StoryView.objects.filter(story=story).count()
            story.save(update_fields=['views_count'])
            self._broadcast_refresh([story.user_id, request.user.id])

        return Response({
            'message': 'تم تسجيل المشاهدة',
            'viewed': True
        })

    @action(detail=True, methods=['get'])
    def viewers(self, request, pk=None):
        """عرض قائمة المشاهدين"""
        story = self.get_object()

        if story.user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية لعرض المشاهدين'},
                status=status.HTTP_403_FORBIDDEN
            )

        views = StoryView.objects.filter(story=story).select_related('user')
        serializer = StoryViewSerializer(views, many=True)
        return Response(serializer.data)

    def _broadcast_story_update(self, story: Story):
        """إرسال إشعار عبر WebSocket عند إضافة استوري"""
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            context = self.get_serializer_context()
            payload = StorySerializer(story, context=context).data

            watcher_ids = set(
                Friend.objects.filter(friend=story.user).values_list('user_id', flat=True)
            )
            watcher_ids.add(story.user_id)

            for user_id in watcher_ids:
                async_to_sync(channel_layer.group_send)(
                    f'user_{user_id}_notifications',
                    {
                        'type': 'stories_refresh',
                        'story': payload if user_id == story.user_id else None,
                    }
                )
        except Exception as exc:
            logger.warning('Failed to broadcast story update: %s', exc)

    def _broadcast_refresh(self, user_ids):
        """طلب تحديث الاستوريات للمستخدمين المحددين"""
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            for user_id in set(user_ids):
                async_to_sync(channel_layer.group_send)(
                    f'user_{user_id}_notifications',
                    {'type': 'stories_refresh'}
                )
        except Exception as exc:
            logger.warning('Failed to broadcast stories refresh: %s', exc)

    # --------------------------------------------------------------------- #
    # وسطاء معالجة الوسائط
    # --------------------------------------------------------------------- #

    def _post_process_story_media(self, story: Story):
        """ضغط ومعالجة الوسائط بعد حفظ القصة."""
        if story.content_type == 'text' or not story.content:
            return

        try:
            if story.content_type == 'image':
                story_config = ImageCompressionConfig(
                    max_edge=self.TARGET_IMAGE_MAX_EDGE,
                    quality=self.IMAGE_QUALITY,
                    min_quality=max(IMAGE_CONFIG.min_quality, self.IMAGE_QUALITY - 10),
                    target_max_kb=IMAGE_CONFIG.target_max_kb,
                    target_min_kb=IMAGE_CONFIG.target_min_kb,
                    allow_webp=IMAGE_CONFIG.allow_webp,
                )
                compressed, _ = compress_image(story.content, config=story_config)
            elif story.content_type == 'video':
                story_video_config = VideoCompressionConfig(
                    target_width=self.TARGET_VIDEO_WIDTH,
                    max_height=VIDEO_CONFIG.max_height,
                    max_bitrate=self.TARGET_VIDEO_BITRATE,
                    min_bitrate=VIDEO_CONFIG.min_bitrate,
                    audio_bitrate=VIDEO_CONFIG.audio_bitrate,
                    frame_rate=VIDEO_CONFIG.frame_rate,
                    max_duration=self.MAX_VIDEO_SECONDS,
                )
                compressed, _ = compress_video(story.content, config=story_video_config)
            else:
                return
        except Exception as exc:
            raise serializers.ValidationError({'content': f'تعذر ضغط الوسائط: {exc}'})

        original_name = Path(story.content.name).stem
        compressed_name = getattr(compressed, 'name', None)
        if not compressed_name:
            suffix = '.mp4' if story.content_type == 'video' else '.jpg'
            compressed_name = f"{original_name}{suffix}"

        story.content.delete(save=False)
        story.content.save(compressed_name, compressed, save=False)
        story.save(update_fields=['content'])


class StoryViewViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet لمشاهدات الاستوريات"""

    serializer_class = StoryViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StoryView.objects.filter(user=self.request.user, story__expires_at__gt=timezone.now()).select_related('story')
