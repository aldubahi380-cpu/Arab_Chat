"""
Views لواجهات الويب
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework.authtoken.models import Token
from .models import ChatRoom, Message, Friend, FriendRequest, Story, Contact, UserProfile, OTPVerification, SessionDevice
from django.db.models import Q, Count, Max
from django.conf import settings


def is_ajax(request):
    """التحقق من أن الطلب AJAX"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def render_spa(request, template_name, context=None):
    """Render template - بسيط بدون SPA"""
    # استخدام render العادي - نظام أبسط وأكثر موثوقية
    return render(request, template_name, context)


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
    from .models import RecentContact, ChatRoom, Message
    from django.db.models import Count
    
    user = request.user
    
    # الحصول على جميع المستخدمين الذين تواصل معهم المستخدم
    recent_contacts = RecentContact.objects.filter(
        user=user
    ).select_related('contact_user', 'contact_user__profile').order_by('-last_message_time')
    
    # إضافة معلومات إضافية لكل مستخدم
    contacts_data = []
    for contact in recent_contacts:
        contact_user = contact.contact_user
        
        # البحث عن غرفة المحادثة بين المستخدمين
        room = ChatRoom.objects.filter(
            is_private=True,
            members=user
        ).filter(members=contact_user).annotate(
            member_count=Count('members')
        ).filter(member_count=2).first()
        
        # الحصول على آخر رسالة
        last_message = None
        unread_count = 0
        if room:
            last_message = Message.objects.filter(room=room).order_by('-created_at').first()
            unread_count = Message.objects.filter(
                room=room
            ).exclude(
                read_by__user=user
            ).count()
        
        contacts_data.append({
            'contact_user': contact_user,
            'room': room,
            'last_message': last_message,
            'unread_count': unread_count,
            'last_message_time': contact.last_message_time,
            'message_count': contact.message_count,
        })
    
    context = {
        'recent_contacts': contacts_data
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
    
    # جميع المجموعات العامة (غير الخاصة)
    all_groups = ChatRoom.objects.filter(is_private=False).annotate(
        member_count=Count('members')
    ).order_by('-created_at')
    
    # المجموعات التي المستخدم عضو فيها
    my_groups = ChatRoom.objects.filter(
        members=user,
        is_private=False
    ).annotate(
        member_count=Count('members')
    )
    
    # إضافة علامة للمجموعات التي المستخدم عضو فيها
    groups_with_status = []
    my_group_ids = set(my_groups.values_list('id', flat=True))
    
    for group in all_groups:
        groups_with_status.append({
            'group': group,
            'is_member': group.id in my_group_ids,
            'member_count': group.member_count
        })
    
    context = {
        'groups': groups_with_status,
        'my_groups': my_groups
    }
    return render_spa(request, 'chat/groups.html', context)


@login_required
def create_group_view(request):
    """إنشاء مجموعة جديدة"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            return JsonResponse({'error': 'اسم المجموعة مطلوب'}, status=400)
        
        # إنشاء المجموعة
        group = ChatRoom.objects.create(
            name=name,
            description=description,
            is_private=False,
            created_by=request.user
        )
        group.members.add(request.user)
        
        return redirect('chat_room', room_id=group.id)
    
    return render_spa(request, 'chat/create_group.html')


@login_required
def join_group_view(request, room_id):
    """الانضمام إلى مجموعة"""
    try:
        room = ChatRoom.objects.get(id=room_id, is_private=False)
        
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
        room = ChatRoom.objects.get(id=room_id, is_private=False)
        
        if request.user in room.members.all():
            # لا يمكن للمنشئ مغادرة المجموعة إلا إذا كان آخر عضو
            if room.created_by == request.user and room.members.count() == 1:
                room.delete()
                return redirect('groups')
            elif room.created_by == request.user:
                return JsonResponse({'error': 'لا يمكن للمنشئ مغادرة المجموعة. يجب تعيين منشئ جديد أولاً'}, status=400)
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
    
    context = {
        'my_stories': my_stories,
        'friends_stories': friends_stories,
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
        
        context = {
            'room': room,
            'messages': messages,
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

