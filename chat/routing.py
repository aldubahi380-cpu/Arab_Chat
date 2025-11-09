from django.urls import re_path
from . import consumers
from . import notifications_consumer
from . import call_consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', notifications_consumer.NotificationsConsumer.as_asgi()),
    re_path(r'ws/call/(?P<call_type>audio|video)/(?P<room_id>\w+)/$', call_consumers.CallSignalingConsumer.as_asgi()),
]

