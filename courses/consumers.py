from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
User = get_user_model()


@database_sync_to_async
def _user_may_reference_course(user_id, course_id):
    """Return True if allowed, False if forbidden, None if course does not exist."""
    from .models import Course, Enrollment

    user = User.objects.get(pk=user_id)
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return None
    if getattr(user, "role", None) == "admin":
        return True
    if course.instructor_id == user.id:
        return True
    return Enrollment.objects.filter(user=user, course=course).exists()


@database_sync_to_async
def _persist_message(sender_id, recipient_id, body, course_id):
    from .models import Message

    text = (body or "").strip()
    if not text:
        raise ValueError("empty_body")
    if len(text) > 10_000:
        raise ValueError("body_too_long")
    sender = User.objects.get(pk=sender_id)
    recipient = User.objects.get(pk=recipient_id)
    if recipient_id == sender_id:
        raise ValueError("self")
    kwargs = {"sender": sender, "recipient": recipient, "body": text}
    if course_id is not None:
        kwargs["course_id"] = int(course_id)
    return Message.objects.create(**kwargs)


@database_sync_to_async
def _message_to_json(message_id):
    from .models import Message
    from .serializers import MessageSerializer

    msg = Message.objects.select_related("sender", "recipient", "course").get(pk=message_id)
    return MessageSerializer(msg).data


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Real-time chat over WebSocket.

    Connect: ``/ws/chat/?token=<access_jwt>``

    Inbound JSON:
      - ``{"type": "ping"}`` → ``{"type": "pong"}``
      - ``{"type": "typing", "recipient": <int>}`` → recipient gets ``{"type": "typing", "from_user": <int>}``
      - ``{"type": "send", "recipient": <int>, "body": "<text>", "course": <int|null>}``

    Outbound JSON:
      - ``{"type": "connected", "user_id": <int>}``
      - ``{"type": "message", "message": { ... same as REST Message ... }}``
      - ``{"type": "typing", "from_user": <int>}`` (from peer)
      - ``{"type": "message_read", ...}`` / ``{"type": "messages_read", ...}`` (read receipts via REST)
      - ``{"type": "error", "detail": "..."}``
    """

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4401)
            return
        self.user = user
        self.group_name = f"chat_user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connected", "user_id": user.id})

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})
            return
        if content.get("type") == "typing":
            recipient_id = content.get("recipient")
            if recipient_id is None:
                await self.send_json(
                    {"type": "error", "detail": "recipient is required for typing"}
                )
                return
            try:
                recipient_id = int(recipient_id)
            except (TypeError, ValueError):
                await self.send_json({"type": "error", "detail": "invalid recipient"})
                return
            if recipient_id == self.user.id:
                return
            await self.channel_layer.group_send(
                f"chat_user_{recipient_id}",
                {"type": "chat.typing", "from_user": self.user.id},
            )
            return
        if content.get("type") != "send":
            await self.send_json(
                {"type": "error", "detail": "expected type send, ping, or typing"}
            )
            return
        recipient_id = content.get("recipient")
        body = (content.get("body") or "").strip()
        course_id = content.get("course")
        if recipient_id is None or not body:
            await self.send_json(
                {"type": "error", "detail": "recipient and body are required"}
            )
            return
        try:
            recipient_id = int(recipient_id)
        except (TypeError, ValueError):
            await self.send_json({"type": "error", "detail": "invalid recipient"})
            return
        if course_id is not None and course_id != "":
            try:
                course_id = int(course_id)
            except (TypeError, ValueError):
                await self.send_json({"type": "error", "detail": "invalid course"})
                return
        else:
            course_id = None

        if course_id is not None:
            allowed = await _user_may_reference_course(self.user.id, course_id)
            if allowed is None:
                await self.send_json({"type": "error", "detail": "course not found"})
                return
            if not allowed:
                await self.send_json(
                    {"type": "error", "detail": "cannot attach this course to the message"}
                )
                return

        try:
            msg = await _persist_message(self.user.id, recipient_id, body, course_id)
        except User.DoesNotExist:
            await self.send_json({"type": "error", "detail": "user not found"})
            return
        except ValueError as e:
            detail = {
                "self": "cannot message yourself",
                "empty_body": "body cannot be empty",
                "body_too_long": "body is too long",
            }.get(str(e), str(e))
            await self.send_json({"type": "error", "detail": detail})
            return

        payload = await _message_to_json(msg.id)
        event = {"type": "chat.message", "payload": {"type": "message", "message": payload}}
        await self.channel_layer.group_send(f"chat_user_{recipient_id}", event)
        await self.send_json({"type": "message", "message": payload})

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    async def chat_notify(self, event):
        await self.send_json(event["payload"])

    async def chat_typing(self, event):
        await self.send_json({"type": "typing", "from_user": event["from_user"]})
