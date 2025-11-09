"""
WebSocket Middleware للـ Token Authentication
"""
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_from_token(token_key):
    """الحصول على المستخدم من Token"""
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware للـ Token Authentication في WebSocket
    """
    async def __call__(self, scope, receive, send):
        # محاولة الحصول على Token من query string
        query_string = parse_qs(scope.get('query_string', b'').decode())
        token = query_string.get('token', [None])[0]
        
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            # إذا لم يكن هناك token، محاولة استخدام session authentication
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    """Stack middleware للـ Token Authentication"""
    from channels.auth import AuthMiddlewareStack
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))

