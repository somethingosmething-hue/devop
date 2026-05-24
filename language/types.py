from __future__ import annotations
from typing import Any, Optional, Callable
import datetime
import re


class DiscordType:
    def __init__(self, name: str, base: Optional[str] = None, properties: dict[str, str] = None, methods: dict[str, Callable] = None):
        self.name = name
        self.base = base
        self.properties = properties or {}
        self.methods = methods or {}

    def can_coerce_to(self, other: str) -> bool:
        if self.name == other:
            return True
        coercion_map = {
            "number": ["text", "string"],
            "integer": ["number", "text", "string"],
            "text": ["string"],
            "string": ["text"],
            "boolean": ["text", "string"],
            "timespan": ["text", "string"],
            "date": ["text", "string"],
            "member": ["user", "text", "string"],
            "user": ["text", "string"],
            "channel": ["text", "string"],
            "textchannel": ["channel", "text", "string"],
            "voicechannel": ["channel", "text", "string"],
            "role": ["text", "string"],
            "guild": ["text", "string"],
            "message": ["text", "string"],
            "emote": ["text", "string"],
            "emoji": ["text", "string"],
            "embed": ["text", "string"],
            "attachment": ["text", "string"],
            "invite": ["text", "string"],
            "sticker": ["text", "string"],
            "scheduledevent": ["text", "string"],
            "button": ["text", "string"],
            "dropdown": ["text", "string"],
            "modal": ["text", "string"],
            "textinput": ["text", "string"],
            "componentrow": ["text", "string"],
            "audiotrack": ["text", "string"],
            "audioplaylist": ["text", "string"],
            "permission": ["text", "string"],
            "webhook": ["text", "string"],
        }
        return other in coercion_map.get(self.name, [])


class TypeRegistry:
    def __init__(self):
        self.types: dict[str, DiscordType] = {}
        self._register_builtins()

    def _register_builtins(self):
        primitives = {
            "text": DiscordType("text", properties={"length": "number", "lowercase": "text", "uppercase": "text"}),
            "string": DiscordType("string", base="text"),
            "number": DiscordType("number"),
            "integer": DiscordType("integer", base="number"),
            "boolean": DiscordType("boolean"),
            "timespan": DiscordType("timespan"),
            "date": DiscordType("date"),
            "list": DiscordType("list", properties={"size": "number", "first": "object", "last": "object", "random": "object"}),
            "object": DiscordType("object"),
        }
        for name, dt in primitives.items():
            self.types[name] = dt

        discord_types = {
            "bot": DiscordType("bot", properties={
                "name": "text", "id": "text", "guilds": "list",
                "presence": "text", "online_status": "text"
            }),
            "user": DiscordType("user", properties={
                "id": "text", "name": "text", "global_name": "text",
                "discriminator": "text", "display_name": "text",
                "avatar": "text", "avatar_url": "text",
                "banner": "text", "banner_url": "text",
                "accent_color": "number", "mention_tag": "text",
                "creation_date": "date", "bot_state": "boolean",
                "flags": "memberflag", "badges": "list",
                "mutual_guilds": "list", "locale": "text",
                "dm_channel": "privatechannel",
            }),
            "member": DiscordType("member", base="user", properties={
                "nickname": "text", "effective_name": "text",
                "roles": "list", "top_role": "role",
                "color": "number", "join_date": "date",
                "boost_date": "date", "voice_channel": "voicechannel",
                "status": "text", "activity": "text",
                "permissions": "permission", "flags": "memberflag",
                "guild": "guild",
            }),
            "guild": DiscordType("guild", properties={
                "id": "text", "name": "text", "icon": "text",
                "icon_url": "text", "banner": "text", "splash": "text",
                "description": "text", "owner": "user",
                "owner_id": "text", "member_count": "number",
                "max_members": "number", "boost_tier": "number",
                "boost_count": "number", "boosters": "list",
                "booster_role": "role", "premium_subscribers": "list",
                "verification_level": "text", "preferred_locale": "text",
                "afk_channel": "voicechannel", "afk_timeout": "timespan",
                "system_channel": "textchannel", "rules_channel": "textchannel",
                "public_updates_channel": "textchannel",
                "channels": "list", "text_channels": "list",
                "voice_channels": "list", "stage_channels": "list",
                "news_channels": "list", "forum_channels": "list",
                "categories": "list", "roles": "list",
                "emotes": "list", "emojis": "list",
                "stickers": "list", "threads": "list",
                "everyone_role": "role", "creation_date": "date",
                "nsfw_level": "text",
            }),
            "message": DiscordType("message", properties={
                "id": "text", "content": "text", "clean_content": "text",
                "author": "user", "member_author": "member",
                "channel": "channel", "guild": "guild",
                "created_at": "date", "edited_at": "date",
                "jump_url": "text", "attachments": "list",
                "embeds": "list", "reactions": "list",
                "emotes": "list", "mentioned_users": "list",
                "mentioned_members": "list", "mentioned_roles": "list",
                "mentioned_channels": "list", "message_type": "text",
                "message_reference": "message", "pinned": "boolean",
                "tts": "boolean", "ephemeral": "boolean",
                "forwarded": "boolean", "activity": "text",
                "reference": "message",
            }),
            "channel": DiscordType("channel", properties={
                "id": "text", "name": "text", "type": "text",
                "guild": "guild", "position": "number",
                "mention_tag": "text", "jump_url": "text",
                "creation_date": "date",
            }),
            "textchannel": DiscordType("textchannel", base="channel", properties={
                "topic": "text", "nsfw": "boolean", "slowmode": "timespan",
                "category": "category", "last_message_id": "text",
                "last_message": "message", "threads": "list",
            }),
            "voicechannel": DiscordType("voicechannel", base="channel", properties={
                "bitrate": "number", "user_limit": "number",
                "members": "list", "category": "category",
                "voice_status": "text", "region": "text",
            }),
            "stagechannel": DiscordType("stagechannel", base="channel", properties={
                "bitrate": "number", "user_limit": "number",
                "category": "category",
            }),
            "newschannel": DiscordType("newschannel", base="textchannel", properties={}),
            "forumchannel": DiscordType("forumchannel", base="channel", properties={
                "topic": "text", "nsfw": "boolean", "slowmode": "timespan",
                "category": "category", "tag_required": "boolean",
                "available_tags": "list",
            }),
            "threadchannel": DiscordType("threadchannel", base="channel", properties={
                "owner_id": "text", "parent": "textchannel",
                "archived": "boolean", "locked": "boolean",
                "public": "boolean", "member_count": "number",
                "total_message_count": "number",
                "auto_archive_duration": "number",
            }),
            "category": DiscordType("category", base="channel", properties={
                "channels": "list", "text_channels": "list",
                "voice_channels": "list",
            }),
            "privatechannel": DiscordType("privatechannel", base="channel", properties={
                "recipient": "user",
            }),
            "role": DiscordType("role", properties={
                "id": "text", "name": "text", "color": "number",
                "hex_color": "text", "position": "number",
                "permissions": "permission", "mentionable": "boolean",
                "hoist": "boolean", "icon": "text",
                "unicode_emoji": "text", "creation_date": "date",
                "mention_tag": "text",
            }),
            "embed": DiscordType("embed", properties={
                "title": "text", "description": "text",
                "color": "number", "author": "text",
                "author_icon": "text", "author_url": "text",
                "image": "text", "thumbnail": "text",
                "footer": "text", "footer_icon": "text",
                "title_url": "text", "timestamp": "date",
                "fields": "list",
            }),
            "emote": DiscordType("emote", properties={
                "id": "text", "name": "text", "animated": "boolean",
                "guild": "guild", "image_url": "text",
            }),
            "emoji": DiscordType("emoji", base="emote"),
            "attachment": DiscordType("attachment", properties={
                "id": "text", "filename": "text",
                "file_extension": "text", "file_url": "text",
                "file_size": "number", "content_type": "text",
                "duration": "number", "spoiler": "boolean",
                "image": "boolean", "audio": "boolean",
                "video": "boolean",
            }),
            "invite": DiscordType("invite", properties={
                "code": "text", "url": "text",
                "uses": "number", "max_uses": "number",
                "max_age": "timespan", "channel": "channel",
                "inviter": "user", "created_at": "date",
                "expires_at": "date", "temporary": "boolean",
            }),
            "slashcommand": DiscordType("slashcommand", properties={
                "id": "text", "name": "text", "description": "text",
            }),
            "slashoption": DiscordType("slashoption"),
            "button": DiscordType("button", properties={
                "id": "text", "label": "text", "style": "text",
                "emoji": "emote", "disabled": "boolean", "url": "text",
            }),
            "dropdown": DiscordType("dropdown", properties={
                "id": "text", "placeholder": "text",
                "min_values": "number", "max_values": "number",
                "options": "list",
            }),
            "modal": DiscordType("modal", properties={
                "title": "text", "id": "text", "rows": "list",
            }),
            "textinput": DiscordType("textinput", properties={
                "id": "text", "label": "text", "placeholder": "text",
                "default_value": "text", "min_length": "number",
                "max_length": "number", "required": "boolean",
            }),
            "componentrow": DiscordType("componentrow", properties={
                "components": "list",
            }),
            "embedtemplate": DiscordType("embedtemplate"),
            "audiotrack": DiscordType("audiotrack", properties={
                "title": "text", "author": "text", "duration": "number",
                "url": "text", "thumbnail": "text", "identifier": "text",
                "source": "text",
            }),
            "audioplaylist": DiscordType("audioplaylist", properties={
                "name": "text", "selected_track": "audiotrack",
                "tracks": "list", "url": "text",
            }),
            "permission": DiscordType("permission", properties={
                "value": "number",
            }),
            "sticker": DiscordType("sticker", properties={
                "id": "text", "name": "text", "description": "text",
                "image_url": "text", "format_type": "text",
                "guild": "guild", "tags": "list",
            }),
            "scheduledevent": DiscordType("scheduledevent", properties={
                "id": "text", "name": "text", "description": "text",
                "start_time": "date", "end_time": "date",
                "channel": "channel", "creator": "user",
                "status": "text", "entity_type": "text",
                "interested_users": "list", "image": "text",
            }),
            "webhook": DiscordType("webhook", properties={
                "id": "text", "name": "text", "avatar": "text",
                "channel": "textchannel", "guild": "guild",
                "token": "text", "url": "text",
            }),
            "memberflag": DiscordType("memberflag"),
            "container": DiscordType("container"),
            "containersection": DiscordType("containersection"),
            "mediagallery": DiscordType("mediagallery"),
            "textdisplay": DiscordType("textdisplay"),
            "forumtag": DiscordType("forumtag", properties={
                "id": "text", "name": "text", "emoji": "emote",
            }),
        }
        for name, dt in discord_types.items():
            self.types[name] = dt

    def get(self, name: str) -> DiscordType | None:
        return self.types.get(name)

    def resolve_property(self, type_name: str, property_name: str) -> str | None:
        dt = self.get(type_name)
        while dt:
            if property_name in dt.properties:
                return dt.properties[property_name]
            dt = self.get(dt.base) if dt.base else None
        return None

    def can_assign(self, value_type: str, target_type: str) -> bool:
        vt = self.get(value_type)
        if vt and vt.can_coerce_to(target_type):
            return True
        return value_type == target_type

    def coerce(self, value: Any, target_type: str) -> Any:
        if value is None:
            return None
        if target_type in ("text", "string"):
            return str(value)
        if target_type == "number":
            try:
                return float(value) if isinstance(value, str) else float(value)
            except (ValueError, TypeError):
                return value
        if target_type == "integer":
            try:
                return int(value) if isinstance(value, str) else int(value)
            except (ValueError, TypeError):
                return value
        if target_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1")
            return bool(value)
        return value


COLORS: dict[str, int] = {
    "blue": 0x3498DB, "red": 0xE74C3C, "green": 0x2ECC71,
    "orange": 0xE67E22, "purple": 0x9B59B6, "yellow": 0xF1C40F,
    "cyan": 0x00BCD4, "pink": 0xE91E63, "white": 0xFFFFFF,
    "black": 0x000000, "gray": 0x95A5A6, "dark_gray": 0x607D8B,
    "light_gray": 0xBDC3C7, "dark_blue": 0x2980B9, "dark_green": 0x27AE60,
    "dark_red": 0xC0392B, "dark_purple": 0x8E44AD, "dark_orange": 0xD35400,
    "teal": 0x1ABC9C, "magenta": 0xE91E63, "brown": 0x795548,
    "blurple": 0x5865F2, "fuchsia": 0xEB008B, "gold": 0xFFD700,
    "lime": 0x00FF00, "maroon": 0x800000, "navy": 0x000080,
    "rainbow": 0x3498DB, "random": 0x3498DB,
}


PERMISSION_NAMES: dict[str, int] = {
    "create_instant_invite": 1 << 0,
    "kick_members": 1 << 1,
    "ban_members": 1 << 2,
    "administrator": 1 << 3,
    "manage_channels": 1 << 4,
    "manage_guild": 1 << 5,
    "add_reactions": 1 << 6,
    "view_audit_log": 1 << 7,
    "priority_speaker": 1 << 8,
    "stream": 1 << 9,
    "read_messages": 1 << 10,
    "view_channel": 1 << 10,
    "send_messages": 1 << 11,
    "send_tts_messages": 1 << 12,
    "manage_messages": 1 << 13,
    "embed_links": 1 << 14,
    "attach_files": 1 << 15,
    "read_message_history": 1 << 16,
    "mention_everyone": 1 << 17,
    "external_emojis": 1 << 18,
    "use_external_emojis": 1 << 18,
    "view_guild_insights": 1 << 19,
    "connect": 1 << 20,
    "speak": 1 << 21,
    "mute_members": 1 << 22,
    "deafen_members": 1 << 23,
    "move_members": 1 << 24,
    "use_vad": 1 << 25,
    "change_nickname": 1 << 26,
    "manage_nicknames": 1 << 27,
    "manage_roles": 1 << 28,
    "manage_permissions": 1 << 28,
    "manage_webhooks": 1 << 29,
    "manage_emojis": 1 << 30,
    "manage_expressions": 1 << 30,
    "use_application_commands": 1 << 31,
    "request_to_speak": 1 << 32,
    "manage_events": 1 << 33,
    "manage_threads": 1 << 34,
    "create_public_threads": 1 << 35,
    "create_private_threads": 1 << 36,
    "send_messages_in_threads": 1 << 37,
    "use_external_stickers": 1 << 38,
    "send_messages_in_thread": 1 << 37,
    "moderate_members": 1 << 40,
}


def parse_timespan(text: str) -> int:
    total = 0
    pattern = re.compile(r"(\d+)\s*(s|sec|second|seconds|m|min|minute|minutes|h|hr|hour|hours|d|day|days|w|week|weeks|mo|month|months|y|year|years)")
    for match in pattern.finditer(str(text)):
        num = int(match.group(1))
        unit = match.group(2)
        if unit in ("s", "sec", "second", "seconds"):
            total += num
        elif unit in ("m", "min", "minute", "minutes"):
            total += num * 60
        elif unit in ("h", "hr", "hour", "hours"):
            total += num * 3600
        elif unit in ("d", "day", "days"):
            total += num * 86400
        elif unit in ("w", "week", "weeks"):
            total += num * 604800
        elif unit in ("mo", "month", "months"):
            total += num * 2592000
        elif unit in ("y", "year", "years"):
            total += num * 31536000
    return total


def format_timespan(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    if seconds < 86400:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
    return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"


def parse_color(value: Any) -> int:
    if isinstance(value, int):
        return value
    s = str(value).lower().strip()
    if s in COLORS:
        return COLORS[s]
    if s.startswith("#"):
        try:
            return int(s[1:], 16)
        except ValueError:
            return COLORS.get("blue", 0x3498DB)
    if s.startswith("0x"):
        try:
            return int(s, 16)
        except ValueError:
            return COLORS.get("blue", 0x3498DB)
    return COLORS.get(s, 0x3498DB)
