"""Conversation list + unread counts derived from Message rows (1:1 threads, optional course)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from .models import Message
from .serializers import UserBriefSerializer

User = get_user_model()


def _course_summary(course, request) -> dict | None:
    if course is None:
        return None
    return {"id": course.id, "title": course.title, "slug": course.slug}


def _preview(body: str, max_len: int = 160) -> str:
    text = (body or "").strip().replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def build_conversation_summaries(
    request_user,
    request,
    *,
    scan_limit: int = 2000,
    max_threads: int = 80,
) -> list[dict]:
    """
    One row per (peer_user, course) pair, ordered by latest activity.
    ``unread_count`` = messages **from peer** to current user not yet read.
    """
    base = (
        Message.objects.filter(Q(sender=request_user) | Q(recipient=request_user))
        .select_related("sender", "recipient", "course")
        .order_by("-created_at")
    )
    last_by_key: dict[tuple[int, int | None], Message] = {}
    for msg in base[:scan_limit]:
        peer_id = msg.recipient_id if msg.sender_id == request_user.id else msg.sender_id
        course_key = msg.course_id
        key = (peer_id, course_key)
        if key not in last_by_key:
            last_by_key[key] = msg

    # One aggregate query for all unread buckets (peer × course), not one COUNT per thread.
    unread_rows = (
        Message.objects.filter(recipient=request_user, read_at__isnull=True)
        .values("sender_id", "course_id")
        .annotate(c=Count("id"))
    )
    unread_map: dict[tuple[int, int | None], int] = {}
    for row in unread_rows:
        cid = row["course_id"]
        unread_map[(row["sender_id"], cid)] = row["c"]

    peer_ids = {k[0] for k in last_by_key}
    peers = User.objects.in_bulk(peer_ids)

    summaries: list[dict] = []
    ctx = {"request": request}
    for (peer_id, course_id), last in last_by_key.items():
        unread_count = unread_map.get((peer_id, course_id), 0)
        peer = peers.get(peer_id)
        if peer is None:
            continue
        summaries.append(
            {
                "peer": UserBriefSerializer(peer, context=ctx).data,
                "course": _course_summary(last.course, request),
                "last_message": {
                    "id": last.id,
                    "sender": last.sender_id,
                    "body_preview": _preview(last.body),
                    "created_at": last.created_at,
                },
                "unread_count": unread_count,
                "updated_at": last.created_at,
            }
        )

    summaries.sort(key=lambda row: row["updated_at"], reverse=True)
    return summaries[:max_threads]
