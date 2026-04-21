"""Push JSON events to a user's WebSocket group (Channels)."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def push_json_to_user(user_id: int, payload: dict) -> None:
    """Deliver ``payload`` to ``chat_user_<id>`` if channel layer is configured."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_user_{user_id}",
        {"type": "chat.notify", "payload": payload},
    )
