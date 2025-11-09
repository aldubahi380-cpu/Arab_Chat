from django.urls import path, include
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserViewSet, UserProfileViewSet, ChatRoomViewSet,
    MessageViewSet, MessageReadViewSet, CallSessionViewSet,
    index_view
)
from .web_views import (
    terms_view, accept_terms_view, register_view,
    dashboard_view,
    private_chats_view, groups_view, search_view,
    stories_view, settings_view, chat_room_view, start_chat_view,
    create_group_view, join_group_view, leave_group_view,
    otp_test_view
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

def redirect_chat_to_chats(request):
    """إعادة توجيه من /chat/ إلى /chats/"""
    return redirect('private_chats')

urlpatterns = [
    path('', index_view, name='index'),
    # صفحات التسجيل
    path('terms/', terms_view, name='terms'),
    path('accept-terms/', accept_terms_view, name='accept_terms'),
    path('register/', register_view, name='register'),
    # واجهات الويب
    path('dashboard/', dashboard_view, name='dashboard'),
    path('chat/', redirect_chat_to_chats, name='chat_redirect'),  # إعادة توجيه من /chat/ إلى /chats/
    path('chats/', private_chats_view, name='private_chats'),
    path('chats/<int:room_id>/', chat_room_view, name='chat_room'),
    path('start-chat/<int:user_id>/', start_chat_view, name='start_chat'),
    path('groups/', groups_view, name='groups'),
    path('groups/create/', create_group_view, name='create_group'),
    path('groups/<int:room_id>/join/', join_group_view, name='join_group'),
    path('groups/<int:room_id>/leave/', leave_group_view, name='leave_group'),
    path('search/', search_view, name='search'),
    path('stories/', stories_view, name='stories'),
    path('settings/', settings_view, name='settings'),
    # واجهة اختبار OTP (للتطوير فقط)
    path('otp-test/', otp_test_view, name='otp_test'),
    # API
    path('api/', include(router.urls)),
    path('api/auth/login/', obtain_auth_token, name='api-login'),
]

