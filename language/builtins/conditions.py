from __future__ import annotations
from language.runtime import Runtime
from language.types import PERMISSION_NAMES
from typing import Any
import random


def register_conditions(runtime: Runtime) -> None:
    h = runtime.condition_handlers

    h["object is set"] = lambda r, a: a[0] is not None
    h["object is not set"] = lambda r, a: a[0] is None
    h["user is bot"] = lambda r, a: hasattr(a[0], 'bot') and a[0].bot if a else False
    h["member has role"] = _cond_member_has_role
    h["member has permission"] = _cond_member_has_permission
    h["member has discord permissions"] = _cond_member_has_discord_permission
    h["member is muted"] = _cond_member_muted
    h["member is deafened"] = _cond_member_deafened
    h["member is timed out"] = _cond_member_timed_out
    h["member is online"] = _cond_member_online
    h["user is owner"] = _cond_user_is_owner
    h["message is edited"] = _cond_message_edited
    h["message is pinned"] = _cond_message_pinned
    h["message is ephemeral"] = _cond_message_ephemeral
    h["message is forwarded"] = _cond_message_forwarded
    h["message is tts"] = _cond_message_tts
    h["message is posted"] = _cond_message_posted
    h["message is from guild"] = _cond_message_from_guild
    h["message is from private"] = _cond_message_from_private
    h["channel is nsfw"] = _cond_channel_nsfw
    h["channel is of type"] = _cond_channel_of_type
    h["thread is archived"] = _cond_thread_archived
    h["thread is locked"] = _cond_thread_locked
    h["thread is public"] = _cond_thread_public
    h["forum is tag required"] = _cond_forum_tag_required
    h["forumchannel is tag required"] = _cond_forum_tag_required
    h["emote is animated"] = _cond_emote_animated
    h["emote is emote"] = _cond_emote_is_emote
    h["bot is loaded"] = _cond_bot_loaded
    h["event is cancelled"] = _cond_event_cancelled
    h["user has banner"] = _cond_user_has_banner
    h["chance"] = _cond_chance
    h["attachment is image"] = lambda r, a: _check_attachment_type(a[0], 'image') if a else False
    h["attachment is audio"] = lambda r, a: _check_attachment_type(a[0], 'audio') if a else False
    h["attachment is video"] = lambda r, a: _check_attachment_type(a[0], 'video') if a else False
    h["attachment is spoiler"] = lambda r, a: getattr(a[0], 'is_spoiler', False)() if a and hasattr(a[0], 'is_spoiler') else (getattr(a[0], 'spoiler', False) if a else False)


def _cond_member_has_role(runtime: Runtime, args: list) -> bool:
    if len(args) < 2:
        return False
    member = args[0]
    role = args[1]
    if hasattr(member, 'roles') and hasattr(role, 'id'):
        return any(r.id == role.id for r in member.roles)
    if isinstance(role, str) and hasattr(member, 'roles'):
        return any(r.name == role or str(r.id) == role for r in member.roles)
    return False


def _cond_member_has_permission(runtime: Runtime, args: list) -> bool:
    if len(args) < 2:
        return False
    member = args[0]
    perm_name = str(args[1])
    if hasattr(member, 'guild_permissions'):
        return getattr(member.guild_permissions, perm_name.replace(" ", "_"), False)
    return False


def _cond_member_has_discord_permission(runtime: Runtime, args: list) -> bool:
    if len(args) < 2:
        return False
    member = args[0]
    perm_name = str(args[1])
    channel = args[2] if len(args) > 2 else None
    if channel is not None and hasattr(member, 'permissions_in'):
        perms = member.permissions_in(channel)
        return getattr(perms, perm_name.replace(" ", "_"), False)
    if hasattr(member, 'guild_permissions'):
        return getattr(member.guild_permissions, perm_name.replace(" ", "_"), False)
    return False


def _cond_member_muted(runtime: Runtime, args: list) -> bool:
    member = args[0] if args else None
    if hasattr(member, 'voice') and member.voice:
        return member.voice.mute or member.voice.self_mute
    return False


def _cond_member_deafened(runtime: Runtime, args: list) -> bool:
    member = args[0] if args else None
    if hasattr(member, 'voice') and member.voice:
        return member.voice.deaf or member.voice.self_deaf
    return False


def _cond_member_timed_out(runtime: Runtime, args: list) -> bool:
    member = args[0] if args else None
    if member is None:
        return False
    if hasattr(member, 'timed_out') and callable(member.timed_out):
        try:
            return member.timed_out()
        except Exception:
            pass
    if hasattr(member, 'timed_out'):
        return bool(member.timed_out)
    if hasattr(member, 'communication_disabled_until'):
        return member.communication_disabled_until is not None
    return False


def _cond_member_online(runtime: Runtime, args: list) -> bool:
    member = args[0] if args else None
    if member is None:
        return False
    if hasattr(member, 'status'):
        return str(member.status) not in ("offline", "invisible")
    return False


def _cond_user_is_owner(runtime: Runtime, args: list) -> bool:
    if len(args) < 2:
        return False
    user = args[0]
    guild = args[1]
    if hasattr(guild, 'owner'):
        return guild.owner and guild.owner.id == getattr(user, 'id', None)
    return False


def _cond_message_edited(runtime: Runtime, args: list) -> bool:
    msg = args[0] if args else None
    if msg is None:
        return False
    return hasattr(msg, 'edited_at') and msg.edited_at is not None


def _cond_message_pinned(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'pinned', False)) if args else False


def _cond_message_ephemeral(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'ephemeral', False)) if args else False


def _cond_message_forwarded(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'forwarded', False)) if args else False


def _cond_message_tts(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'tts', False)) if args else False


def _cond_message_posted(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'crossposted', False)) if args else False


def _cond_message_from_guild(runtime: Runtime, args: list) -> bool:
    msg = args[0] if args else None
    return msg is not None and getattr(msg, 'guild', None) is not None


def _cond_message_from_private(runtime: Runtime, args: list) -> bool:
    msg = args[0] if args else None
    return msg is not None and getattr(msg, 'guild', None) is None


def _cond_channel_nsfw(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'nsfw', False)) if args else False


def _cond_channel_of_type(runtime: Runtime, args: list) -> bool:
    if len(args) < 2:
        return False
    channel = args[0]
    type_name = str(args[1]).lower().replace(" ", "_")
    if hasattr(channel, 'type'):
        import discord
        type_map = {
            "text": discord.ChannelType.text,
            "voice": discord.ChannelType.voice,
            "stage": discord.ChannelType.stage_voice,
            "news": discord.ChannelType.news,
            "forum": discord.ChannelType.forum,
            "category": discord.ChannelType.category,
            "thread": discord.ChannelType.public_thread,
            "public_thread": discord.ChannelType.public_thread,
            "private_thread": discord.ChannelType.private_thread,
            "announcement_thread": discord.ChannelType.news_thread,
        }
        target = type_map.get(type_name)
        if target:
            return channel.type == target
        return str(channel.type) == type_name
    return False


def _cond_thread_archived(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'archived', False)) if args else False


def _cond_thread_locked(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'locked', False)) if args else False


def _cond_thread_public(runtime: Runtime, args: list) -> bool:
    thread = args[0] if args else None
    if thread is None:
        return False
    if hasattr(thread, 'type'):
        import discord
        return thread.type in (discord.ChannelType.public_thread, discord.ChannelType.news_thread)
    return False


def _cond_forum_tag_required(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'require_tag', False)) if args else False


def _cond_emote_animated(runtime: Runtime, args: list) -> bool:
    return bool(getattr(args[0], 'animated', False)) if args else False


def _cond_emote_is_emote(runtime: Runtime, args: list) -> bool:
    return args[0] is not None if args else False


def _cond_bot_loaded(runtime: Runtime, args: list) -> bool:
    return args[0] is not None if args else False


def _cond_event_cancelled(runtime: Runtime, args: list) -> bool:
    return runtime.event_context.cancelled


def _cond_user_has_banner(runtime: Runtime, args: list) -> bool:
    user = args[0] if args else None
    return user is not None and hasattr(user, 'banner') and user.banner is not None


def _cond_chance(runtime: Runtime, args: list) -> bool:
    if not args:
        return True
    try:
        pct = float(args[0])
        return random.random() * 100 < pct
    except (TypeError, ValueError):
        return True


def _check_attachment_type(attachment: Any, type_name: str) -> bool:
    if attachment is None:
        return False
    ct = getattr(attachment, 'content_type', "") or ""
    if type_name == 'image':
        return ct.startswith('image/')
    if type_name == 'audio':
        return ct.startswith('audio/')
    if type_name == 'video':
        return ct.startswith('video/')
    return False
