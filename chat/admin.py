from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, ChatRoom, Message, MessageRead,
    OTPVerification, FriendRequest, Friend, BlockedUser,
    Story, StoryView, Contact, DeviceToken, RecentContact
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'ملف المستخدم'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'is_online', 'last_seen', 'created_at')
    list_filter = ('is_online', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_private', 'created_by', 'member_count', 'created_at')
    list_filter = ('is_private', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    filter_horizontal = ('members',)
    readonly_fields = ('created_at', 'updated_at')

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'عدد الأعضاء'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'content_preview', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at', 'room')
    search_fields = ('content', 'sender__username', 'room__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'محتوى الرسالة'


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('user__username', 'message__content')
    readonly_fields = ('read_at',)


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'otp_code', 'is_verified', 'expires_at', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('phone', 'otp_code')
    readonly_fields = ('created_at',)


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ('user', 'friend', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'friend__username')
    readonly_fields = ('created_at',)


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'blocked_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'blocked_user__username')
    readonly_fields = ('created_at',)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'views_count', 'expires_at', 'created_at')
    list_filter = ('content_type', 'created_at', 'expires_at')
    search_fields = ('user__username', 'caption')
    readonly_fields = ('views_count', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ('story', 'user', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('story__user__username', 'user__username')
    readonly_fields = ('viewed_at',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'name', 'is_registered', 'registered_user', 'synced_at')
    list_filter = ('is_registered', 'synced_at', 'created_at')
    search_fields = ('user__username', 'phone', 'name')
    readonly_fields = ('synced_at', 'created_at')


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'device_name', 'is_active', 'last_used', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at', 'last_used')
    search_fields = ('user__username', 'device_id', 'device_name', 'token')
    readonly_fields = ('last_used', 'created_at')
    list_editable = ('is_active',)


@admin.register(RecentContact)
class RecentContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact_user', 'message_count', 'last_message_time', 'created_at')
    list_filter = ('created_at', 'last_message_time')
    search_fields = ('user__username', 'contact_user__username')
    readonly_fields = ('last_message_time', 'created_at')
    date_hierarchy = 'last_message_time'


# إلغاء تسجيل User الافتراضي وإعادة تسجيله مع التعديلات
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# تخصيص لوحة الإدارة
admin.site.site_header = 'لوحة إدارة عرب شات'
admin.site.site_title = 'عرب شات - لوحة الإدارة'
admin.site.index_title = 'لوحة التحكم'
