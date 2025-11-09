"""
Views لإدارة المستخدمين المتواصل معهم (RecentContacts)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import RecentContact
from .serializers import RecentContactSerializer


class RecentContactViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet للمستخدمين المتواصل معهم"""
    queryset = RecentContact.objects.all()
    serializer_class = RecentContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """الحصول على المستخدمين المتواصل معهم للمستخدم الحالي"""
        return RecentContact.objects.filter(user=self.request.user).select_related(
            'contact_user', 'contact_user__profile'
        ).order_by('-last_message_time')
    
    @action(detail=False, methods=['get'])
    def my_contacts(self, request):
        """قائمة المستخدمين المتواصل معهم"""
        contacts = self.get_queryset()
        serializer = self.get_serializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """حذف جميع المستخدمين المتواصل معهم"""
        RecentContact.objects.filter(user=request.user).delete()
        return Response({'message': 'تم حذف جميع المستخدمين المتواصل معهم'})
    
    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        """إزالة مستخدم من قائمة المتواصل معهم"""
        recent_contact = self.get_object()
        
        if recent_contact.user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية لإزالة هذا المستخدم'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        recent_contact.delete()
        return Response({'message': 'تم إزالة المستخدم من قائمة المتواصل معهم'})

