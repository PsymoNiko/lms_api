"""
ASGI config for core project (HTTP + WebSocket via Django Channels).
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

django_asgi_app = get_asgi_application()

from courses.middleware_jwt_ws import JWTQueryAuthMiddleware  # noqa: E402
from courses.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTQueryAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
