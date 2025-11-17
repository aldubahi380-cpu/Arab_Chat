from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserViewSet, UserProfileViewSet, ChatRoomViewSet,
    MessageViewSet, MessageReadViewSet, CallSessionViewSet,
)
from .auth_views import OTPVerificationViewSet
from .friends_views import FriendRequestViewSet, FriendViewSet, BlockedUserViewSet
from .stories_views import StoryViewSet, StoryViewViewSet
from .contacts_views import ContactViewSet
from .push_notifications_views import DeviceTokenViewSet
from .recent_contacts_views import RecentContactViewSet
from .session_views import SessionDeviceViewSet

router = DefaultRouter()
# المستخدمون والملفات
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='profile')
# الدردشة
router.register(r'rooms', ChatRoomViewSet, basename='room')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'message-reads', MessageReadViewSet, basename='message-read')
router.register(r'calls', CallSessionViewSet, basename='call')
# التحقق والتسجيل
router.register(r'otp', OTPVerificationViewSet, basename='otp')
# الصداقات
router.register(r'friend-requests', FriendRequestViewSet, basename='friend-request')
router.register(r'friends', FriendViewSet, basename='friend')
router.register(r'blocked-users', BlockedUserViewSet, basename='blocked-user')
# الاستوريات
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'story-views', StoryViewViewSet, basename='story-view')
# جهات الاتصال
router.register(r'contacts', ContactViewSet, basename='contact')
# إشعارات Push
router.register(r'device-tokens', DeviceTokenViewSet, basename='device-token')
# جلسات الأجهزة
router.register(r'session-devices', SessionDeviceViewSet, basename='session-device')
# المستخدمون المتواصل معهم
router.register(r'recent-contacts', RecentContactViewSet, basename='recent-contact')

urlpatterns = [
    # API فقط - لا توجد واجهات ويب
    path('api/', include(router.urls)),
    path('api/auth/login/', obtain_auth_token, name='api-login'),
]

