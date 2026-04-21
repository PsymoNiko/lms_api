"""Create in-app notifications and optionally push to the user's WebSocket group."""

from __future__ import annotations

from .models import Notification
from .ws_notify import push_json_to_user


def _serialize_notification(n: Notification) -> dict:
    from .serializers import NotificationSerializer

    return NotificationSerializer(n).data


def create_notification(
    user,
    *,
    kind: str,
    title: str,
    body: str = "",
    payload: dict | None = None,
    push_ws: bool = True,
) -> Notification:
    n = Notification.objects.create(
        user=user,
        kind=kind,
        title=title[:255],
        body=body or "",
        payload=payload or {},
    )
    if push_ws:
        push_json_to_user(
            user.id,
            {"type": "notification", "notification": _serialize_notification(n)},
        )
    return n


def preview_text(text: str, max_len: int = 200) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"
