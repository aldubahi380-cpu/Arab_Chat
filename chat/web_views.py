"""
Views لواجهات الويب
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.utils import timezone
from rest_framework.authtoken.models import Token
from .models import ChatRoom, Message, Friend, FriendRequest, Story, Contact, UserProfile, OTPVerification, SessionDevice, RecentContact
from .stories_views import build_channels_context_for_user
from django.db.models import Q, Count, Max
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
import json


def is_ajax(request):
    """التحقق من أن الطلب AJAX"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def render_spa(request, template_name, context=None):
    """Render template - بسيط بدون SPA"""
    # استخدام render العادي - نظام أبسط وأكثر موثوقية
    return render(request, template_name, context)


CHAT_MEDIA_LABELS = {
    'image': 'صورة',
    'video': 'فيديو',
    'audio': 'رسالة صوتية',
    'file': 'ملف',
}

CHAT_MEDIA_ICON_CLASSES = {
    'image': 'app-icon--media-image',
    'video': 'app-icon--media-video',
    'audio': 'app-icon--media-audio',
    'file': 'app-icon--media-file',
}


def build_chat_threads_payload(user):
    """تجهيز بيانات الدردشات للمستخدم مع معاينة مشابهة لواتساب."""
    from django.db.models import Count

    recent_contacts = RecentContact.objects.filter(
        user=user
    ).select_related('contact_user', 'contact_user__profile').order_by('-last_message_time')

    contacts_data = []
    for contact in recent_contacts:
        contact_user = contact.contact_user

        room = ChatRoom.objects.filter(
            is_private=True,
            members=user
        ).filter(members=contact_user).annotate(
            member_count=Count('members')
        ).filter(member_count=2).first()

        last_message = None
        unread_count = 0
        if room:
            last_message = Message.objects.filter(room=room).select_related('sender').order_by('-created_at').first()
            unread_count = Message.objects.filter(room=room).exclude(read_by__user=user).count()

        try:
            contact_profile = contact_user.profile
        except UserProfile.DoesNotExist:
            contact_profile = None

        def build_preview_text(message):
            if not message:
                return ''
            if message.is_deleted:
                return 'تم حذف هذه الرسالة'
            content = (message.content or '').strip()
            if message.message_type == 'text':
                return content
            label = CHAT_MEDIA_LABELS.get(message.message_type, 'محتوى')
            if content:
                snippet = content[:70]
                if len(content) > 70:
                    snippet = f"{snippet.rstrip()}…"
                return f"{label} · {snippet}"
            return label

        def resolve_delivery_status(message, partner_id):
            if not message or message.sender_id != user.id:
                return None
            if message.is_read:
                return 'read'
            try:
                read_by_ids = set(message.read_by.values_list('user_id', flat=True))
            except Exception:
                read_by_ids = set()
            if partner_id in read_by_ids:
                return 'read'
            return 'sent'

        preview_text = build_preview_text(last_message)
        message_type = last_message.message_type if last_message else None
        delivery_status = resolve_delivery_status(last_message, contact_user.id if last_message else None)
        last_activity = (last_message.created_at if last_message else contact.last_message_time)
        media_icon_class = CHAT_MEDIA_ICON_CLASSES.get(message_type)

        contacts_data.append({
            'contact_user': contact_user,
            'contact_profile': contact_profile,
            'room': room,
            'last_message': last_message,
            'unread_count': unread_count,
            'last_message_time': contact.last_message_time,
            'message_count': contact.message_count,
            'is_pinned': contact.is_pinned,
            'pinned_at': contact.pinned_at,
            'is_muted': False,
            'search_text': f"{contact_user.username} {preview_text}".strip(),
            'last_activity_iso': last_activity.isoformat() if last_activity else '',
            'last_message_meta': {
                'is_mine': bool(last_message and last_message.sender_id == user.id),
                'status': delivery_status,
                'status_icon_class': 'app-icon--status-seen' if delivery_status == 'read' else 'app-icon--status-sent' if delivery_status else '',
                'media_icon_class': media_icon_class or '',
                'media_label': CHAT_MEDIA_LABELS.get(message_type, '') if message_type in CHAT_MEDIA_LABELS else '',
                'message_type': message_type or '',
                'preview_text': preview_text,
            },
            'thread_kind': (room.room_type if room and room.room_type else 'private') if room else 'private',
            'is_active': False,
        })

    pinned_threads = sorted(
        [c for c in contacts_data if c['is_pinned']],
        key=lambda item: item.get('pinned_at') or item.get('last_message_time'),
        reverse=True
    )
    regular_threads = [c for c in contacts_data if not c['is_pinned']]

    return {
        'pinned': pinned_threads,
        'regular': regular_threads,
    }


def terms_view(request):
    """صفحة الشروط والخصوصية"""
    # إذا كان المستخدم مسجل دخول، توجيهه للصفحة الرئيسية مباشرة
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    from datetime import datetime
    context = {
        'current_date': datetime.now()
    }
    return render_spa(request, 'chat/terms.html', context)


def accept_terms_view(request):
    """قبول الشروط والانتقال لصفحة التسجيل"""
    # إذا كان المستخدم مسجل دخول، توجيهه للصفحة الرئيسية مباشرة
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        accept = request.POST.get('accept')
        if accept:
            # حفظ في session أن المستخدم قبل الشروط
            request.session['terms_accepted'] = True
            return redirect('register')
        else:
            return render_spa(request, 'chat/terms.html', {
                'error': 'يجب الموافقة على الشروط أولاً'
            })
    return redirect('terms')


def register_view(request):
    """صفحة إنشاء الحساب"""
    # إذا كان المستخدم مسجل دخول، توجيهه للصفحة الرئيسية مباشرة
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # التحقق من قبول الشروط
    if not request.session.get('terms_accepted'):
        return redirect('terms')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # التحقق من البيانات
        if not username or len(username) < 3:
            return render_spa(request, 'chat/register.html', {
                'error': 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل'
            })
        
        if not phone:
            return render_spa(request, 'chat/register.html', {
                'error': 'رقم الهاتف مطلوب'
            })
        
        # التحقق من عدم وجود اسم مستخدم أو رقم هاتف موجود
        if User.objects.filter(username=username).exists():
            return render_spa(request, 'chat/register.html', {
                'error': 'اسم المستخدم موجود بالفعل. يرجى اختيار اسم آخر'
            })
        
        if UserProfile.objects.filter(phone=phone).exists():
            return render_spa(request, 'chat/register.html', {
                'error': 'رقم الهاتف موجود بالفعل. يرجى استخدام رقم آخر'
            })
        
        try:
            # إنشاء المستخدم بدون كلمة مرور (في مرحلة التطوير)
            user = User.objects.create_user(
                username=username,
                email=f'{phone}@arabchat.com'  # استخدام رقم الهاتف كبريد إلكتروني
            )
            # تعطيل كلمة المرور في مرحلة التطوير
            user.set_unusable_password()
            user.save()
            
            # إنشاء ملف المستخدم
            profile = UserProfile.objects.create(
                user=user,
                phone=phone,
                is_verified=True  # في مرحلة التطوير، نعتبر الحساب موثق تلقائياً
            )
            
            # تسجيل الدخول التلقائي
            login(request, user)
            
            # إنشاء token للـ API
            token_obj, _ = Token.objects.get_or_create(user=user)

            # إنشاء جلسة جهاز وتعيين الكوكيز الضرورية
            device_name = request.POST.get('device_name') or request.META.get('HTTP_USER_AGENT', '')[:255]
            platform = request.POST.get('platform') or 'web'
            session_device = SessionDevice.issue_for_request(
                user=user,
                request=request,
                device_name=device_name,
                platform=platform
            )

            # حذف session قبول الشروط
            request.session.pop('terms_accepted', None)

            response = redirect('dashboard')
            max_age = 60 * 60 * 24 * 90  # 90 يوم
            response.set_cookie('session_token', session_device.session_token, max_age=max_age, httponly=False, samesite='Lax')
            response.set_cookie('session_device_id', session_device.device_id, max_age=max_age, httponly=False, samesite='Lax')
            response.set_cookie('auth_token', token_obj.key, max_age=max_age, httponly=False, samesite='Lax')

            try:
                request.session['session_device_id'] = session_device.device_id
            except Exception:
                pass

            return response
            
        except Exception as e:
            return render_spa(request, 'chat/register.html', {
                'error': f'حدث خطأ أثناء إنشاء الحساب: {str(e)}'
            })
    
    return render_spa(request, 'chat/register.html')


@login_required
def dashboard_view(request):
    """الصفحة الرئيسية - رسالة ترحيبية فقط"""
    return render_spa(request, 'chat/dashboard.html')


@login_required
def private_chats_view(request):
    """واجهة الدردشة الخاصة - عرض قائمة المستخدمين المتواصل معهم"""
    user = request.user
    threads_payload = build_chat_threads_payload(user)

    context = {
        'chat_threads': threads_payload['regular'],
        'pinned_threads': threads_payload['pinned'],
        'communities_preview': [],
    }
    return render_spa(request, 'chat/private_chats.html', context)


@login_required
def start_chat_view(request, user_id):
    """بدء محادثة جديدة مع مستخدم"""
    from .models import ChatRoom, RecentContact
    from django.db.models import Count
    from django.shortcuts import get_object_or_404
    from django.contrib.auth.models import User
    
    user = request.user
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == user:
        from django.shortcuts import redirect
        return redirect('private_chats')
    
    # البحث عن غرفة محادثة موجودة
    room = ChatRoom.objects.filter(
        is_private=True,
        members=user
    ).filter(members=target_user).annotate(
        member_count=Count('members')
    ).filter(member_count=2).first()
    
    # إذا لم تكن هناك غرفة، إنشاء واحدة جديدة
    if not room:
        room = ChatRoom.objects.create(
            name=f"{user.username} - {target_user.username}",
            is_private=True,
            created_by=user
        )
        room.members.add(user, target_user)
        
        # إضافة إلى RecentContact
        RecentContact.objects.get_or_create(
            user=user,
            contact_user=target_user
        )
        RecentContact.objects.get_or_create(
            user=target_user,
            contact_user=user
        )
    
    # إعادة التوجيه إلى صفحة المحادثة
    from django.shortcuts import redirect
    return redirect('chat_room', room_id=room.id)


@login_required
def groups_view(request):
    """واجهة المجموعات - عرض جميع المجموعات العامة"""
    user = request.user
    
    communities_qs = ChatRoom.objects.filter(
        room_type=ChatRoom.ROOM_TYPE_COMMUNITY
    ).annotate(
        member_count=Count('members')
    ).order_by('-created_at')
    my_communities_ids = set(
        ChatRoom.objects.filter(
            room_type=ChatRoom.ROOM_TYPE_COMMUNITY,
            members=user
        ).values_list('id', flat=True)
    )
    communities = [
        {
            'room': community,
            'member_count': community.member_count,
            'is_member': community.id in my_communities_ids,
        }
        for community in communities_qs
    ]

    user_groups_qs = ChatRoom.objects.filter(
        room_type=ChatRoom.ROOM_TYPE_GROUP,
        members=user
    ).annotate(
        member_count=Count('members')
    ).select_related('created_by').prefetch_related('members')

    group_cards = []
    for group in user_groups_qs:
        group_cards.append({
            'room': group,
            'member_count': group.member_count,
            'is_owner': group.created_by_id == user.id,
            'invite_link': group.get_invite_link(request),
            'invite_code': group.invite_code,
            'member_usernames': list(group.members.exclude(id=user.id).values_list('username', flat=True)[:6]),
            'member_ids': list(group.members.values_list('id', flat=True)),
        })

    friends = Friend.objects.filter(user=user).select_related('friend')
    friend_options = []
    for friend in friends:
        avatar_url = None
        try:
            profile = friend.friend.profile
        except UserProfile.DoesNotExist:
            profile = None
        if profile and profile.avatar:
            avatar_url = profile.avatar.url
        friend_options.append({
            'id': friend.friend.id,
            'username': friend.friend.username,
            'avatar': avatar_url,
        })
    friends = Friend.objects.filter(user=user).select_related('friend')
    friend_options = []
    for friend in friends:
        avatar_url = None
        try:
            profile = friend.friend.profile
        except UserProfile.DoesNotExist:
            profile = None
        if profile and profile.avatar:
            avatar_url = profile.avatar.url
        friend_options.append({
            'id': friend.friend.id,
            'username': friend.friend.username,
            'avatar': avatar_url,
        })

    context = {
        'communities': communities,
        'group_cards': group_cards,
        'friend_options': json.dumps(friend_options, ensure_ascii=False),
        'group_cards_json': json.dumps([
            {
                'id': card['room'].id,
                'member_ids': card['member_ids'],
            }
            for card in group_cards
        ], ensure_ascii=False),
        'has_groups': bool(group_cards),
    }
    return render_spa(request, 'chat/groups.html', context)


@login_required
def create_group_view(request):
    """إنشاء مجموعة جديدة"""
    friends = Friend.objects.filter(user=request.user).select_related('friend', 'friend__profile')
    friend_options = [
        {
            'id': friend.friend.id,
            'username': friend.friend.username,
            'avatar': friend.friend.profile.avatar.url if hasattr(friend.friend, 'profile') and friend.friend.profile.avatar else None,
        }
        for friend in friends
    ]

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        member_ids = request.POST.getlist('members')

        if not name:
            return JsonResponse({'error': 'اسم المجموعة مطلوب'}, status=400)

        # إنشاء المجموعة
        group = ChatRoom.objects.create(
            name=name,
            description=description,
            room_type=ChatRoom.ROOM_TYPE_GROUP,
            created_by=request.user
        )
        group.members.add(request.user)
        if member_ids:
            users_to_add = User.objects.filter(id__in=member_ids).exclude(id=request.user.id)
            group.members.add(*users_to_add)

        return redirect('chat_room', room_id=group.id)

    context = {
        'friend_options': json.dumps(friend_options, ensure_ascii=False),
    }
    return render_spa(request, 'chat/create_group.html', context)


@login_required
def join_group_view(request, room_id):
    """الانضمام إلى مجموعة"""
    try:
        room = ChatRoom.objects.get(id=room_id, room_type=ChatRoom.ROOM_TYPE_COMMUNITY)
        
        if request.user not in room.members.all():
            room.members.add(request.user)
            return redirect('chat_room', room_id=room.id)
        else:
            # المستخدم عضو بالفعل
            return redirect('chat_room', room_id=room.id)
    except ChatRoom.DoesNotExist:
        return redirect('groups')


@login_required
def leave_group_view(request, room_id):
    """مغادرة مجموعة"""
    try:
        room = ChatRoom.objects.get(id=room_id, room_type=ChatRoom.ROOM_TYPE_COMMUNITY)
        
        if request.user in room.members.all():
            # لا يمكن للمنشئ مغادرة المجموعة إلا إذا كان آخر عضو
            if room.created_by == request.user and room.members.count() == 1:
                room.delete()
                return redirect('groups')
            elif room.created_by == request.user:
                return JsonResponse({'error': 'لا يمكن للمنشئ مغادرة المجتمع. يجب تعيين منشئ جديد أولاً'}, status=400)
            else:
                room.members.remove(request.user)
                return redirect('groups')
        else:
            return redirect('groups')
    except ChatRoom.DoesNotExist:
        return redirect('groups')


@login_required
def search_view(request):
    """واجهة البحث"""
    user = request.user
    
    # الأصدقاء
    friends = Friend.objects.filter(user=user).select_related('friend')
    
    # المحظورون
    from .models import BlockedUser
    blocked_users = BlockedUser.objects.filter(user=user).select_related('blocked_user')
    
    # طلبات الصداقة المستلمة
    received_requests = FriendRequest.objects.filter(
        to_user=user,
        status='pending'
    ).select_related('from_user')
    
    # الطلبات المرسلة
    sent_requests = FriendRequest.objects.filter(
        from_user=user,
        status='pending'
    ).select_related('to_user')
    
    context = {
        'friends': friends,
        'blocked_users': blocked_users,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    }
    return render_spa(request, 'chat/search.html', context)


@login_required
def stories_view(request):
    """واجهة الاستوريات"""
    user = request.user
    
    # استورياتي
    my_stories = Story.objects.filter(
        user=user,
        expires_at__gt=timezone.now()
    )
    
    # استوريات الأصدقاء
    from .models import Friend
    friends = Friend.objects.filter(user=user).values_list('friend', flat=True)
    friends_stories = Story.objects.filter(
        user__in=friends,
        expires_at__gt=timezone.now()
    ).select_related('user')
    
    channels_context = build_channels_context_for_user(user)

    context = {
        'my_stories': my_stories,
        'friends_stories': friends_stories,
        'channels_following': channels_context['following'],
        'channels_suggested': channels_context['suggested'],
    }
    return render_spa(request, 'chat/stories.html', context)


@login_required
def settings_view(request):
    """واجهة الإعدادات"""
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render_spa(request, 'chat/settings.html', context)


@login_required
def chat_room_view(request, room_id):
    """واجهة غرفة الدردشة"""
    try:
        room = ChatRoom.objects.get(id=room_id, members=request.user)
        messages = Message.objects.filter(room=room).select_related('sender').order_by('created_at')
        
        # التحقق من الأمان - المستخدم يجب أن يكون عضواً في الغرفة
        if request.user not in room.members.all():
            return redirect('private_chats')
        
        pinned_messages = Message.objects.filter(room=room, is_pinned=True).order_by('-pinned_at', '-created_at')[:3]
        is_chat_pinned = False
        other_member = room.members.exclude(id=request.user.id).first()
        if room.is_private and other_member:
            try:
                contact_entry = RecentContact.objects.get(user=request.user, contact_user=other_member)
                is_chat_pinned = contact_entry.is_pinned
            except RecentContact.DoesNotExist:
                is_chat_pinned = False

        threads_payload = build_chat_threads_payload(request.user)
        sidebar_pinned_threads = threads_payload['pinned']
        sidebar_regular_threads = threads_payload['regular']

        for thread in sidebar_pinned_threads + sidebar_regular_threads:
            is_active = bool(thread.get('room') and thread['room'] and thread['room'].id == room.id)
            thread['is_active'] = is_active

        context = {
            'room': room,
            'messages': messages,
            'pinned_messages': pinned_messages,
            'is_chat_pinned': is_chat_pinned,
            'sidebar_pinned_threads': sidebar_pinned_threads,
            'sidebar_regular_threads': sidebar_regular_threads,
            'active_room_id': room.id,
            'other_member': other_member,
        }
        return render_spa(request, 'chat/chat_room.html', context)
    except ChatRoom.DoesNotExist:
        return redirect('private_chats')


@login_required
def start_chat_view(request, user_id):
    """بدء محادثة جديدة مع مستخدم"""
    try:
        target_user = User.objects.get(id=user_id)
        
        # التحقق من وجود غرفة محادثة خاصة موجودة
        existing_room = ChatRoom.objects.filter(
            is_private=True,
            members=request.user
        ).filter(members=target_user).distinct()
        
        # إذا كانت الغرفة تحتوي على عضوين فقط (محادثة خاصة)
        for room in existing_room:
            if room.members.count() == 2:
                return redirect('chat_room', room_id=room.id)
        
        # إنشاء غرفة جديدة
        room = ChatRoom.objects.create(
            name=f"{request.user.username} - {target_user.username}",
            is_private=True,
            created_by=request.user
        )
        room.members.add(request.user, target_user)
        RecentContact.objects.get_or_create(
            user=request.user,
            contact_user=target_user
        )
        RecentContact.objects.get_or_create(
            user=target_user,
            contact_user=request.user
        )
        
        return redirect('chat_room', room_id=room.id)
    except User.DoesNotExist:
        return redirect('search')


def otp_test_view(request):
    """واجهة اختبار لعرض رموز OTP (للتطوير فقط)"""
    # التحقق من أننا في وضع التطوير
    if not getattr(settings, 'DEBUG', False):
        return redirect('dashboard')
    
    # الحصول على آخر 20 رمز OTP
    otps = OTPVerification.objects.all().order_by('-created_at')[:20]
    
    context = {
        'otps': otps,
        'is_dev': True,
        'dev_otp_code': '123456'
    }
    
    return render_spa(request, 'chat/otp_test.html', context)


@require_GET
def service_worker(request):
    """تقديم ملف Service Worker من الجذر لضمان نطاق التطبيق الكامل."""
    sw_filename = getattr(settings, 'PWA_SERVICE_WORKER_FILE', 'pwa/sw.js')
    try:
        with staticfiles_storage.open(sw_filename) as fh:
            content = fh.read()
    except Exception:
        return HttpResponse('// service worker not found', content_type='application/javascript', status=404)

    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def join_group_by_code_view(request, invite_code):
    """الانضمام إلى مجموعة خاصة باستخدام رمز الدعوة من خلال الواجهة"""
    try:
        room = ChatRoom.objects.get(invite_code=invite_code, room_type=ChatRoom.ROOM_TYPE_GROUP)
    except ChatRoom.DoesNotExist:
        return redirect('groups')

    if request.user not in room.members.all():
        room.members.add(request.user)
    return redirect('chat_room', room_id=room.id)

