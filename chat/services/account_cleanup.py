from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q

from rest_framework.authtoken.models import Token

from ..models import (
    BlockedUser,
    ChatRoom,
    Contact,
    DeviceToken,
    Friend,
    FriendRequest,
    Message,
    MessageRead,
    OTPVerification,
    RecentContact,
    SessionDevice,
    Story,
    StoryView,
)

logger = logging.getLogger(__name__)


def _cleanup_chat_rooms_for_user(user) -> None:
    """Remove user from chat rooms and delete orphaned ones."""
    # Rooms created by the user
    rooms_created = ChatRoom.objects.filter(created_by=user)
    for room in rooms_created:
        # Remove the user first so counts are accurate
        room.members.remove(user)
        remaining_members = room.members.count()
        if room.is_private and remaining_members <= 1:
            room.delete()
        elif remaining_members == 0:
            room.delete()

    # Rooms where the user is just a member
    other_rooms = (
        ChatRoom.objects.filter(members=user)
        .exclude(created_by=user)
        .annotate(member_count=Count('members'))
    )
    for room in other_rooms:
        room.members.remove(user)
        remaining_members = room.members.count()
        if room.is_private and remaining_members <= 1:
            room.delete()
        elif remaining_members == 0:
            room.delete()


def _cleanup_recent_contacts(user) -> None:
    """Remove recent contact links involving the user."""
    RecentContact.objects.filter(Q(user=user) | Q(contact_user=user)).delete()


def _cleanup_contacts(user) -> None:
    """Remove address-book style contacts for the user."""
    Contact.objects.filter(user=user).delete()
    Contact.objects.filter(registered_user=user).update(
        registered_user=None, is_registered=False
    )


def _cleanup_story_data(user) -> None:
    Story.objects.filter(user=user).delete()
    StoryView.objects.filter(user=user).delete()


def _cleanup_social_graph(user) -> None:
    FriendRequest.objects.filter(Q(from_user=user) | Q(to_user=user)).delete()
    Friend.objects.filter(Q(user=user) | Q(friend=user)).delete()
    BlockedUser.objects.filter(Q(user=user) | Q(blocked_user=user)).delete()


def _cleanup_devices_and_sessions(user) -> None:
    DeviceToken.objects.filter(user=user).delete()
    SessionDevice.objects.filter(user=user).delete()


def _cleanup_messages(user) -> None:
    Message.objects.filter(sender=user).delete()
    MessageRead.objects.filter(user=user).delete()


def _cleanup_otps(user) -> None:
    profile = getattr(user, 'profile', None)
    if profile and profile.phone:
        OTPVerification.objects.filter(phone=profile.phone).delete()


def delete_user_account(user_id: int) -> bool:
    """Remove a user and all related application data."""
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.info("User %s already deleted.", user_id)
        return False

    username = user.username

    try:
        with transaction.atomic():
            _cleanup_messages(user)
            _cleanup_chat_rooms_for_user(user)
            _cleanup_social_graph(user)
            _cleanup_story_data(user)
            _cleanup_contacts(user)
            _cleanup_recent_contacts(user)
            _cleanup_devices_and_sessions(user)
            _cleanup_otps(user)

            Token.objects.filter(user=user).delete()

            user.delete()
    except Exception:
        logger.exception("Error deleting account for user %s", username)
        raise

    logger.info("Successfully deleted account for user %s", username)
    return True

