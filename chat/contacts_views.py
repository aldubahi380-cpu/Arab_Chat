"""
Views لمزامنة جهات الاتصال
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Contact, UserProfile
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet لجهات الاتصال"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على جهات اتصال المستخدم الحالي"""
        return Contact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """إنشاء جهة اتصال"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """مزامنة جهات الاتصال"""
        contacts_data = request.data.get('contacts', [])
        
        if not contacts_data:
            return Response(
                {'error': 'يجب إرسال قائمة جهات الاتصال'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        synced_count = 0
        registered_count = 0
        
        for contact_data in contacts_data:
            phone = contact_data.get('phone')
            name = contact_data.get('name', '')
            
            if not phone:
                continue
            
            # التحقق من وجود المستخدم بهذا الرقم
            try:
                profile = UserProfile.objects.get(phone=phone)
                registered_user = profile.user
                is_registered = True
                registered_count += 1
            except UserProfile.DoesNotExist:
                registered_user = None
                is_registered = False
            
            # إنشاء أو تحديث جهة الاتصال
            contact, created = Contact.objects.update_or_create(
                user=request.user,
                phone=phone,
                defaults={
                    'name': name,
                    'is_registered': is_registered,
                    'registered_user': registered_user,
                    'synced_at': timezone.now()
                }
            )
            
            synced_count += 1
        
        return Response({
            'message': 'تمت المزامنة بنجاح',
            'synced_count': synced_count,
            'registered_count': registered_count
        })
    
    @action(detail=False, methods=['get'])
    def registered(self, request):
        """جهات الاتصال المسجلة في التطبيق"""
        contacts = Contact.objects.filter(
            user=request.user,
            is_registered=True
        ).select_related('registered_user')
        
        serializer = self.get_serializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """حذف جميع جهات الاتصال"""
        Contact.objects.filter(user=request.user).delete()
        return Response({'message': 'تم حذف جميع جهات الاتصال'})

