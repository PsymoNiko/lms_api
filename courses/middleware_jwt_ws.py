"""JWT from WebSocket query `?token=<access>` for Channels."""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_access_token(token_string):
    if not token_string:
        return AnonymousUser()
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    User = get_user_model()
    try:
        access = AccessToken(token_string)
        uid = access["user_id"]
        return User.objects.get(pk=uid)
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTQueryAuthMiddleware(BaseMiddleware):
    """Sets ``scope['user']`` from ``?token=<SimpleJWT access>`` on WebSocket handshakes."""

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            query = parse_qs(scope.get("query_string", b"").decode())
            token = (query.get("token") or [None])[0]
            scope["user"] = await _user_from_access_token(token)
        return await super().__call__(scope, receive, send)
