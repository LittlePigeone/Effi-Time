import os
import django
from presentation.websocket.urls import routes

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'effi_time.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from django.core.asgi import get_asgi_application


django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        SessionMiddlewareStack(
            URLRouter(routes=routes)
        )
    )
})