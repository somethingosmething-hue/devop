from __future__ import annotations
from language.runtime import Runtime, Scope
from language.types import parse_color, parse_timespan, format_timespan, PERMISSION_NAMES, COLORS
from typing import Any, Optional
import datetime
import random
import math
import re as re_module


def register_expressions(runtime: Runtime) -> None:
    h = runtime.expression_handlers

    h["bot"] = _expr_bot
    h["bots"] = _expr_bots
    h["user"] = _expr_user
    h["member"] = _expr_member
    h["guild"] = _expr_guild
    h["channel"] = _expr_channel
    h["text channel"] = _expr_text_channel
    h["voice channel"] = _expr_voice_channel
    h["stage channel"] = _expr_stage_channel
    h["forum channel"] = _expr_forum_channel
    h["thread channel"] = _expr_thread_channel
    h["category"] = _expr_category
    h["role"] = _expr_role
    h["emote"] = _expr_emote
    h["emoji"] = _expr_emoji
    h["sticker"] = _expr_sticker
    h["embed"] = _expr_embed
    h["invite"] = _expr_invite
    h["webhook"] = _expr_webhook
    h["scheduledevent"] = _expr_scheduledevent

    h["id of"] = _expr_id
    h["name of"] = _expr_name
    h["mention tag of"] = _expr_mention
    h["jump url of"] = _expr_jump_url
    h["avatar of"] = _expr_avatar
    h["avatar url of"] = _expr_avatar_url
    h["banner of"] = _expr_banner
    h["banner url of"] = _expr_banner_url
    h["accent color of"] = _expr_accent_color
    h["global name of"] = _expr_global_name
    h["display name of"] = _expr_display_name
    h["effective name of"] = _expr_effective_name
    h["nickname of"] = _expr_nickname
    h["discriminator of"] = _expr_discriminator
    h["creation date of"] = _expr_creation_date
    h["created at of"] = _expr_created_at
    h["content of"] = _expr_content
    h["clean content of"] = _expr_clean_content
    h["topic of"] = _expr_topic
    h["slowmode of"] = _expr_slowmode
    h["bitrate of"] = _expr_bitrate
    h["user limit of"] = _expr_user_limit
    h["nsfw state of"] = _expr_nsfw_state
    h["position of"] = _expr_position
    h["parent of"] = _expr_parent
    h["channel of"] = _expr_channel_of
    h["guild of"] = _expr_guild_of
    h["author of"] = _expr_author
    h["member author of"] = _expr_member_author
    h["top role of"] = _expr_top_role
    h["color of"] = _expr_color_of
    h["hex color of"] = _expr_hex_color
    h["icon of"] = _expr_icon
    h["icon url of"] = _expr_icon_url
    h["splash of"] = _expr_splash
    h["owner of"] = _expr_owner
    h["owner id of"] = _expr_owner_id
    h["member count of"] = _expr_member_count
    h["boost tier of"] = _expr_boost_tier
    h["boost count of"] = _expr_boost_count
    h["booster role of"] = _expr_booster_role
    h["everyone role of"] = _expr_everyone
    h["bot role of"] = _expr_bot_role
    h["join date of"] = _expr_join_date
    h["boost date of"] = _expr_boost_date
    h["voice channel of"] = _expr_voice_channel_of
    h["status of"] = _expr_status_of
    h["activity of"] = _expr_activity_of
    h["flags of"] = _expr_flags_of
    h["badges of"] = _expr_badges_of
    h["mutual guilds of"] = _expr_mutual_guilds
    h["user locale of"] = _expr_user_locale
    h["preferred locale of"] = _expr_preferred_locale
    h["verification level of"] = _expr_verification_level
    h["file name of"] = _expr_file_name
    h["file url of"] = _expr_file_url
    h["file size of"] = _expr_file_size
    h["content type of"] = _expr_content_type
    h["animated state of"] = _expr_animated_state
    h["image url of"] = _expr_image_url
    h["invite code"] = _expr_invite_code
    h["invite url"] = _expr_invite_url
    h["uses of"] = _expr_uses_of
    h["max uses of"] = _expr_max_uses
    h["max age of"] = _expr_max_age
    h["inviter of"] = _expr_inviter_of
    h["expires at of"] = _expr_expires_at
    h["temporary state of"] = _expr_temporary_state

    h["argument"] = _expr_argument
    h["used command"] = _expr_used_command
    h["used prefix"] = _expr_used_prefix
    h["used argument"] = _expr_used_argument

    h["length of"] = _expr_length
    h["size of"] = _expr_size
    h["first of"] = _expr_first
    h["first element of"] = _expr_first
    h["last of"] = _expr_last
    h["last element of"] = _expr_last
    h["random of"] = _expr_random
    h["random element of"] = _expr_random
    h["max of"] = _expr_max
    h["min of"] = _expr_min
    h["sum of"] = _expr_sum
    h["average of"] = _expr_average
    h["index of"] = _expr_index

    h["now"] = _expr_now
    h["round of"] = _expr_round
    h["floor of"] = _expr_floor
    h["ceil of"] = _expr_ceil
    h["absolute of"] = _expr_abs
    h["absolute value of"] = _expr_abs
    h["sqrt of"] = _expr_sqrt
    h["root of"] = _expr_sqrt
    h["sin of"] = _expr_sin
    h["cos of"] = _expr_cos
    h["tan of"] = _expr_tan
    h["random number between"] = _expr_random_between

    h["parsed as"] = _expr_parsed
    h["split by"] = _expr_split
    h["joined by"] = _expr_join
    h["lowercase"] = _expr_lower
    h["uppercase"] = _expr_upper
    h["trimmed"] = _expr_trim
    h["subtext"] = _expr_subtext
    h["replaced"] = _expr_replaced
    h["hex"] = _expr_hex
    h["color from hex"] = _expr_color_from_hex
    h["timespan_from"] = _expr_timespan_from
    h["percent"] = _expr_percent

    h["selected values"] = _expr_selected_values
    h["selected entities"] = _expr_selected_entities
    h["value of text input with id"] = _expr_text_input_value
    h["values of dropdown with id"] = _expr_dropdown_values

    h["permission"] = _expr_permission
    h["discord permissions of"] = _expr_discord_permissions

    h["members of"] = _expr_members_of
    h["roles of"] = _expr_roles_of
    h["channels of"] = _expr_channels_of
    h["emotes of"] = _expr_emotes_of
    h["emojis of"] = _expr_emotes_of
    h["text channels of"] = _expr_text_channels_of
    h["voice channels of"] = _expr_voice_channels_of
    h["stage channels of"] = _expr_stage_channels_of
    h["forum channels of"] = _expr_forum_channels_of
    h["categories of"] = _expr_categories_of
    h["bans of"] = _expr_bans_of
    h["invites of"] = _expr_invites_of
    h["webhooks of"] = _expr_webhooks_of
    h["stickers of"] = _expr_stickers_of
    h["threads of"] = _expr_threads_of
    h["boosters of"] = _expr_boosters_of
    h["premium subscribers of"] = _expr_premium_subscribers

    h["all members"] = _expr_all_members
    h["all players"] = _expr_all_members
    h["all guilds"] = _expr_all_guilds
    h["all channels"] = _expr_all_channels
    h["all roles"] = _expr_all_roles
    h["all bots"] = _expr_all_bots


def _expr_bot(runtime: Runtime, args: list) -> Any:
    if not args:
        return runtime.event_context.get("bot")
    name = str(args[0])
    return runtime.bot_instances.get(name)


def _expr_bots(runtime: Runtime, args: list) -> list:
    return list(runtime.bot_instances.values())


def _expr_user(runtime: Runtime, args: list) -> Any:
    if len(args) >= 1 and args[0]:
        return args[0]
    return runtime.event_context.get("user")


def _expr_member(runtime: Runtime, args: list) -> Any:
    if len(args) >= 2:
        return None
    if args:
        return args[0]
    return runtime.event_context.get("member")


def _expr_guild(runtime: Runtime, args: list) -> Any:
    if args:
        return args[0]
    return runtime.event_context.get("guild")


def _expr_channel(runtime: Runtime, args: list) -> Any:
    if args:
        return args[0]
    return runtime.event_context.get("channel")


def _expr_text_channel(runtime: Runtime, args: list) -> Any:
    name = str(args[0]) if args else ""
    guild = args[1] if len(args) > 1 else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'text_channels'):
        for ch in guild.text_channels:
            if ch.name == name:
                return ch
    return None


def _expr_voice_channel(runtime: Runtime, args: list) -> Any:
    name = str(args[0]) if args else ""
    guild = args[1] if len(args) > 1 else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'voice_channels'):
        for ch in guild.voice_channels:
            if ch.name == name:
                return ch
    return None


def _expr_stage_channel(runtime: Runtime, args: list) -> Any:
    name = str(args[0]) if args else ""
    guild = args[1] if len(args) > 1 else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'stage_channels'):
        for ch in guild.stage_channels:
            if ch.name == name:
                return ch
    return None


def _expr_forum_channel(runtime: Runtime, args: list) -> Any:
    name = str(args[0]) if args else ""
    guild = args[1] if len(args) > 1 else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'forum_channels'):
        for ch in guild.forum_channels:
            if ch.name == name:
                return ch
    return None


def _expr_thread_channel(runtime: Runtime, args: list) -> Any:
    name = str(args[0]) if args else ""
    guild = args[1] if len(args) > 1 else runtime.event_context.get("guild")
    if guild:
        for ch in guild.threads:
            if ch.name == name:
                return ch
    return None


def _expr_category(runtime: Runtime, args: list) -> Any:
    name = str(args[0]) if args else ""
    guild = args[1] if len(args) > 1 else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'categories'):
        for cat in guild.categories:
            if cat.name == name:
                return cat
    return None


def _expr_role(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("role")


def _expr_emote(runtime: Runtime, args: list) -> Any:
    if len(args) >= 1:
        name = str(args[0])
        guild = args[1] if len(args) > 1 else runtime.event_context.get("guild")
        if guild and hasattr(guild, 'emojis'):
            for emoji in guild.emojis:
                if emoji.name == name:
                    return emoji
    return runtime.event_context.get("emote")


def _expr_emoji(runtime: Runtime, args: list) -> Any:
    return _expr_emote(runtime, args)


def _expr_sticker(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("sticker")


def _expr_embed(runtime: Runtime, args: list) -> Any:
    return None


def _expr_invite(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("invite")


def _expr_webhook(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("webhook")


def _expr_scheduledevent(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("scheduledevent")


def _resolve_attr(obj: Any, attr: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if hasattr(obj, attr):
        val = getattr(obj, attr)
        return val() if callable(val) else val
    return default


def _expr_id(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return None
    if hasattr(obj, 'id'):
        return str(obj.id)
    if isinstance(obj, dict):
        return obj.get('id')
    return str(obj)


def _expr_name(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return None
    if hasattr(obj, 'name'):
        return obj.name
    if isinstance(obj, dict):
        return obj.get('name')
    return str(obj)


def _expr_mention(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return ""
    if hasattr(obj, 'mention'):
        return obj.mention
    return f"<@{obj}>" if obj else ""


def _expr_jump_url(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return ""
    if hasattr(obj, 'jump_url'):
        return obj.jump_url
    return ""


def _expr_avatar(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    return _resolve_attr(obj, 'avatar')


def _expr_avatar_url(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return ""
    if hasattr(obj, 'display_avatar'):
        return str(obj.display_avatar.url)
    if hasattr(obj, 'avatar_url'):
        return str(obj.avatar.url) if obj.avatar else ""
    return ""


def _expr_banner(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    return _resolve_attr(obj, 'banner')


def _expr_banner_url(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return ""
    if hasattr(obj, 'banner') and obj.banner:
        return str(obj.banner.url)
    return ""


def _expr_accent_color(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'accent_color') if args else None


def _expr_global_name(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'global_name', "") if args else ""


def _expr_display_name(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'display_name', "") if args else ""


def _expr_effective_name(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'display_name', "") if args else ""


def _expr_nickname(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'nick', "") if args else ""


def _expr_discriminator(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'discriminator', "") if args else ""


def _expr_creation_date(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'created_at') if args else None


def _expr_created_at(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'created_at') if args else None


def _expr_content(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'content', "") if args else ""


def _expr_clean_content(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'clean_content', "") if args else ""


def _expr_topic(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'topic', "") if args else ""


def _expr_slowmode(runtime: Runtime, args: list) -> Any:
    val = _resolve_attr(args[0], 'slowmode_delay', 0) if args else 0
    return val


def _expr_bitrate(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'bitrate', 0) if args else 0


def _expr_user_limit(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'user_limit', 0) if args else 0


def _expr_nsfw_state(runtime: Runtime, args: list) -> bool:
    return bool(_resolve_attr(args[0], 'nsfw', False)) if args else False


def _expr_position(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'position', 0) if args else 0


def _expr_parent(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'category') if args else None


def _expr_channel_of(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'channel') if args else None


def _expr_guild_of(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'guild') if args else None


def _expr_author(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'author') if args else None


def _expr_member_author(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'author') if args else None


def _expr_top_role(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'top_role') if args else None


def _expr_color_of(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'color') if args else None


def _expr_hex_color(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return "#000000"
    if hasattr(obj, 'color') and obj.color:
        return str(obj.color)
    if hasattr(obj, 'colour') and obj.colour:
        return str(obj.colour)
    return "#000000"


def _expr_icon(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'icon') if args else None


def _expr_icon_url(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return ""
    if hasattr(obj, 'icon') and obj.icon:
        return str(obj.icon.url)
    if hasattr(obj, 'icon_url'):
        return str(obj.icon_url)
    return ""


def _expr_splash(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if obj is None:
        return ""
    if hasattr(obj, 'splash') and obj.splash:
        return str(obj.splash.url)
    if hasattr(obj, 'splash_url'):
        return str(obj.splash_url)
    return ""


def _expr_owner(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'owner') if args else runtime.event_context.get("guild_owner")


def _expr_owner_id(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'owner_id') if args else None


def _expr_member_count(runtime: Runtime, args: list) -> int:
    return _resolve_attr(args[0], 'member_count', 0) if args else 0


def _expr_boost_tier(runtime: Runtime, args: list) -> int:
    return _resolve_attr(args[0], 'premium_tier', 0) if args else 0


def _expr_boost_count(runtime: Runtime, args: list) -> int:
    return _resolve_attr(args[0], 'premium_subscription_count', 0) if args else 0


def _expr_booster_role(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'premium_subscriber_role') if args else None


def _expr_everyone(runtime: Runtime, args: list) -> Any:
    guild = args[0] if args else runtime.event_context.get("guild")
    if hasattr(guild, 'default_role'):
        return guild.default_role
    return None


def _expr_bot_role(runtime: Runtime, args: list) -> Any:
    guild = args[0] if args else runtime.event_context.get("guild")
    bot = args[1] if len(args) > 1 else runtime.current_bot
    if guild and bot and hasattr(guild, 'get_member'):
        member = guild.get_member(bot.user.id if hasattr(bot, 'user') else 0)
        if member and hasattr(member, 'top_role'):
            return member.top_role
    return None


def _expr_join_date(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'joined_at') if args else None


def _expr_boost_date(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'premium_since') if args else None


def _expr_voice_channel_of(runtime: Runtime, args: list) -> Any:
    member = args[0] if args else None
    if member and hasattr(member, 'voice') and member.voice:
        return member.voice.channel
    return None


def _expr_status_of(runtime: Runtime, args: list) -> Any:
    member = args[0] if args else None
    if member and hasattr(member, 'raw_status'):
        return member.raw_status
    if member and hasattr(member, 'status'):
        return str(member.status)
    return "offline"


def _expr_activity_of(runtime: Runtime, args: list) -> Any:
    member = args[0] if args else None
    if member and hasattr(member, 'activity') and member.activity:
        return member.activity.name
    return ""


def _expr_flags_of(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'public_flags') if args else None


def _expr_badges_of(runtime: Runtime, args: list) -> list:
    flags = _resolve_attr(args[0], 'public_flags') if args else None
    if flags:
        return [flag.name for flag in flags.all()]
    return []


def _expr_mutual_guilds(runtime: Runtime, args: list) -> list:
    return list(_resolve_attr(args[0], 'mutual_guilds', [])) if args else []


def _expr_user_locale(runtime: Runtime, args: list) -> str:
    return _resolve_attr(args[0], 'locale', "") if args else ""


def _expr_preferred_locale(runtime: Runtime, args: list) -> str:
    return _resolve_attr(args[0], 'preferred_locale', "") if args else ""


def _expr_verification_level(runtime: Runtime, args: list) -> str:
    obj = args[0] if args else None
    if obj is None:
        return "none"
    if hasattr(obj, 'verification_level'):
        return str(obj.verification_level)
    return "none"


def _expr_file_name(runtime: Runtime, args: list) -> str:
    return _resolve_attr(args[0], 'filename', "") if args else ""


def _expr_file_url(runtime: Runtime, args: list) -> str:
    obj = args[0] if args else None
    if obj and hasattr(obj, 'url'):
        return str(obj.url)
    return ""


def _expr_file_size(runtime: Runtime, args: list) -> int:
    return _resolve_attr(args[0], 'size', 0) if args else 0


def _expr_content_type(runtime: Runtime, args: list) -> str:
    return _resolve_attr(args[0], 'content_type', "") if args else ""


def _expr_animated_state(runtime: Runtime, args: list) -> bool:
    return bool(_resolve_attr(args[0], 'animated', False)) if args else False


def _expr_image_url(runtime: Runtime, args: list) -> str:
    obj = args[0] if args else None
    if obj and hasattr(obj, 'url'):
        return str(obj.url)
    return ""


def _expr_invite_code(runtime: Runtime, args: list) -> str:
    return _resolve_attr(args[0], 'code', "") if args else ""


def _expr_invite_url(runtime: Runtime, args: list) -> str:
    obj = args[0] if args else None
    if obj and hasattr(obj, 'url'):
        return str(obj.url)
    return ""


def _expr_uses_of(runtime: Runtime, args: list) -> int:
    return _resolve_attr(args[0], 'uses', 0) if args else 0


def _expr_max_uses(runtime: Runtime, args: list) -> int:
    return _resolve_attr(args[0], 'max_uses', 0) if args else 0


def _expr_max_age(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'max_age') if args else None


def _expr_inviter_of(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'inviter') if args else None


def _expr_expires_at(runtime: Runtime, args: list) -> Any:
    return _resolve_attr(args[0], 'expires_at') if args else None


def _expr_temporary_state(runtime: Runtime, args: list) -> bool:
    return bool(_resolve_attr(args[0], 'temporary', False)) if args else False


def _expr_argument(runtime: Runtime, args: list) -> Any:
    if not args:
        return None
    name = str(args[0])
    val = runtime.local_vars.get(f"arg-{name}")
    if val is not None:
        return val
    val = runtime.event_context.values.get(f"arg-{name}")
    if val is not None:
        return val
    return runtime.local_vars.get(name)


def _expr_used_command(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("command_name")


def _expr_used_prefix(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("prefix")


def _expr_used_argument(runtime: Runtime, args: list) -> Any:
    return runtime.event_context.get("used_argument") or ""


def _expr_length(runtime: Runtime, args: list) -> int:
    obj = args[0] if args else ""
    return len(str(obj)) if obj else 0


def _expr_size(runtime: Runtime, args: list) -> int:
    obj = args[0] if args else None
    if obj is None:
        return 0
    if hasattr(obj, '__len__'):
        return len(obj)
    if isinstance(obj, dict):
        return len(obj)
    return 0


def _expr_first(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if isinstance(obj, (list, tuple)) and obj:
        return obj[0]
    if isinstance(obj, dict) and obj:
        return list(obj.values())[0]
    return None


def _expr_last(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if isinstance(obj, (list, tuple)) and obj:
        return obj[-1]
    if isinstance(obj, dict) and obj:
        return list(obj.values())[-1]
    return None


def _expr_random(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else None
    if isinstance(obj, (list, tuple)) and obj:
        return random.choice(obj)
    if isinstance(obj, dict) and obj:
        return random.choice(list(obj.values()))
    return None


def _expr_max(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else []
    if isinstance(obj, (list, tuple)) and obj:
        return max(obj)
    return 0


def _expr_min(runtime: Runtime, args: list) -> Any:
    obj = args[0] if args else []
    if isinstance(obj, (list, tuple)) and obj:
        return min(obj)
    return 0


def _expr_sum(runtime: Runtime, args: list) -> float:
    obj = args[0] if args else []
    if isinstance(obj, (list, tuple)):
        return sum(float(x) for x in obj if x is not None)
    return 0


def _expr_average(runtime: Runtime, args: list) -> float:
    obj = args[0] if args else []
    if isinstance(obj, (list, tuple)) and obj:
        vals = [float(x) for x in obj if x is not None]
        return sum(vals) / len(vals) if vals else 0
    return 0


def _expr_index(runtime: Runtime, args: list) -> int:
    if len(args) < 2:
        return -1
    val = args[0]
    lst = args[1]
    if isinstance(lst, (list, tuple)):
        try:
            return lst.index(val)
        except ValueError:
            return -1
    return -1


def _expr_now(runtime: Runtime, args: list) -> datetime.datetime:
    return datetime.datetime.now()


def _expr_round(runtime: Runtime, args: list) -> int:
    val = float(args[0]) if args else 0
    return round(val)


def _expr_floor(runtime: Runtime, args: list) -> int:
    val = float(args[0]) if args else 0
    return math.floor(val)


def _expr_ceil(runtime: Runtime, args: list) -> int:
    val = float(args[0]) if args else 0
    return math.ceil(val)


def _expr_abs(runtime: Runtime, args: list) -> float:
    val = float(args[0]) if args else 0
    return abs(val)


def _expr_sqrt(runtime: Runtime, args: list) -> float:
    val = float(args[0]) if args else 0
    return math.sqrt(val)


def _expr_sin(runtime: Runtime, args: list) -> float:
    val = float(args[0]) if args else 0
    return math.sin(val)


def _expr_cos(runtime: Runtime, args: list) -> float:
    val = float(args[0]) if args else 0
    return math.cos(val)


def _expr_tan(runtime: Runtime, args: list) -> float:
    val = float(args[0]) if args else 0
    return math.tan(val)


def _expr_random_between(runtime: Runtime, args: list) -> float:
    if len(args) < 2:
        return 0
    try:
        low = float(args[0])
        high = float(args[1])
        return random.uniform(low, high)
    except (TypeError, ValueError):
        return 0


def _expr_parsed(runtime: Runtime, args: list) -> Any:
    if len(args) < 2:
        return None
    val = str(args[0])
    target_type = str(args[1]).lower()
    if target_type in ("number", "integer"):
        try:
            return int(val) if target_type == "integer" else float(val)
        except ValueError:
            return 0
    if target_type == "text":
        return val
    if target_type == "boolean":
        return val.lower() in ("true", "yes", "1")
    return val


def _expr_split(runtime: Runtime, args: list) -> list:
    if len(args) < 2:
        return []
    text = str(args[0])
    sep = str(args[1])
    return text.split(sep)


def _expr_join(runtime: Runtime, args: list) -> str:
    if len(args) < 2:
        return ""
    lst = args[0] if isinstance(args[0], (list, tuple)) else []
    sep = str(args[1])
    return sep.join(str(x) for x in lst)


def _expr_lower(runtime: Runtime, args: list) -> str:
    return str(args[0]).lower() if args else ""


def _expr_upper(runtime: Runtime, args: list) -> str:
    return str(args[0]).upper() if args else ""


def _expr_trim(runtime: Runtime, args: list) -> str:
    return str(args[0]).strip() if args else ""


def _expr_subtext(runtime: Runtime, args: list) -> str:
    if len(args) < 2:
        return str(args[0]) if args else ""
    text = str(args[0])
    start = int(args[1]) - 1 if args[1] else 0
    end = int(args[2]) if len(args) > 2 and args[2] is not None else len(text)
    return text[start:end]


def _expr_replaced(runtime: Runtime, args: list) -> str:
    if len(args) < 3:
        return str(args[0]) if args else ""
    text = str(args[0])
    old = str(args[1])
    new = str(args[2])
    return text.replace(old, new)


def _expr_hex(runtime: Runtime, args: list) -> int:
    val = str(args[0]) if args else "000000"
    return parse_color(f"#{val}")


def _expr_color_from_hex(runtime: Runtime, args: list) -> int:
    val = str(args[0]) if args else "#3498DB"
    return parse_color(val)


def _expr_timespan_from(runtime: Runtime, args: list) -> Any:
    if len(args) < 2:
        return 0
    amount = float(args[0]) if args[0] else 0
    unit = str(args[1]).lower()
    multipliers = {
        "millisecond": 0.001, "milliseconds": 0.001,
        "tick": 0.05, "ticks": 0.05,
        "second": 1, "seconds": 1,
        "minute": 60, "minutes": 60,
        "hour": 3600, "hours": 3600,
        "day": 86400, "days": 86400,
        "week": 604800, "weeks": 604800,
        "month": 2592000, "months": 2592000,
        "year": 31536000, "years": 31536000,
    }
    return amount * multipliers.get(unit, 1)


def _expr_percent(runtime: Runtime, args: list) -> float:
    val = float(args[0]) if args else 0
    return val / 100.0


def _expr_selected_values(runtime: Runtime, args: list) -> list:
    return runtime.event_context.get("selected_values", [])


def _expr_selected_entities(runtime: Runtime, args: list) -> list:
    return runtime.event_context.get("selected_entities", [])


def _expr_text_input_value(runtime: Runtime, args: list) -> Any:
    input_id = str(args[0]) if args else ""
    interaction = runtime.event_context.get("interaction")
    if interaction and hasattr(interaction, 'data') and interaction.data:
        try:
            data = interaction.data
            if isinstance(data, dict):
                for row in data.get("components", []):
                    for comp in row.get("components", []):
                        if comp.get("custom_id") == input_id:
                            return comp.get("value", "")
                for row in data.get("components", []):
                    for comp in row.get("components", []):
                        if comp.get("custom_id") == "components" and isinstance(comp.get("components"), list):
                            for sub in comp["components"]:
                                if sub.get("custom_id") == input_id:
                                    return sub.get("value", "")
        except (AttributeError, KeyError, TypeError):
            pass
    return None


def _expr_dropdown_values(runtime: Runtime, args: list) -> list:
    dd_id = str(args[0]) if args else ""
    interaction = runtime.event_context.get("interaction")
    if interaction and hasattr(interaction, 'data') and interaction.data:
        try:
            data = interaction.data
            if isinstance(data, dict):
                for row in data.get("components", []):
                    for comp in row.get("components", []):
                        if comp.get("custom_id") == dd_id:
                            return comp.get("values", [])
        except (AttributeError, KeyError, TypeError):
            pass
    return []


def _expr_permission(runtime: Runtime, args: list) -> int:
    name = str(args[0]) if args else ""
    return PERMISSION_NAMES.get(name.lower(), 0)


def _expr_discord_permissions(runtime: Runtime, args: list) -> Any:
    if not args:
        return 0
    member = args[0]
    channel = args[1] if len(args) > 1 else None
    if channel is not None and hasattr(member, 'permissions_in'):
        return member.permissions_in(channel)
    if hasattr(member, 'guild_permissions'):
        return member.guild_permissions
    if hasattr(member, 'permissions'):
        return member.permissions
    return 0


def _expr_members_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'members'):
        return list(obj.members)
    if isinstance(obj, dict):
        return list(obj.values())
    return []


def _expr_roles_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'roles'):
        return list(obj.roles)
    return []


def _expr_channels_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'channels'):
        return list(obj.channels)
    return []


def _expr_emotes_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'emojis'):
        return list(obj.emojis)
    return []


def _expr_text_channels_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'text_channels'):
        return list(obj.text_channels)
    return []


def _expr_voice_channels_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'voice_channels'):
        return list(obj.voice_channels)
    return []


def _expr_stage_channels_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'stage_channels'):
        return list(obj.stage_channels)
    return []


def _expr_forum_channels_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'forum_channels'):
        return list(obj.forum_channels)
    return []


def _expr_categories_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'categories'):
        return list(obj.categories)
    return []


def _expr_bans_of(runtime: Runtime, args: list) -> list:
    return []


def _expr_invites_of(runtime: Runtime, args: list) -> list:
    return []


def _expr_webhooks_of(runtime: Runtime, args: list) -> list:
    return []


def _expr_stickers_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'stickers'):
        return list(obj.stickers)
    return []


def _expr_threads_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'threads'):
        return list(obj.threads)
    return []


def _expr_boosters_of(runtime: Runtime, args: list) -> list:
    obj = args[0] if args else None
    if obj is None:
        return []
    if hasattr(obj, 'premium_subscribers'):
        return list(obj.premium_subscribers)
    return []


def _expr_premium_subscribers(runtime: Runtime, args: list) -> list:
    return _expr_boosters_of(runtime, args)


def _expr_all_members(runtime: Runtime, args: list) -> list:
    guild = args[0] if args else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'members'):
        return list(guild.members)
    return []


def _expr_all_guilds(runtime: Runtime, args: list) -> list:
    bot = args[0] if args else runtime.current_bot
    if bot and hasattr(bot, 'guilds'):
        return list(bot.guilds)
    return []


def _expr_all_channels(runtime: Runtime, args: list) -> list:
    guild = args[0] if args else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'channels'):
        return list(guild.channels)
    return []


def _expr_all_roles(runtime: Runtime, args: list) -> list:
    guild = args[0] if args else runtime.event_context.get("guild")
    if guild and hasattr(guild, 'roles'):
        return list(guild.roles)
    return []


def _expr_all_bots(runtime: Runtime, args: list) -> list:
    return list(runtime.bot_instances.values())
