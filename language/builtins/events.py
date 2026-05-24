from typing import Any


EVENT_DEFINITIONS: dict[str, dict[str, Any]] = {
    "bot ready": {"values": ["bot", "bot_name"]},
    "guild ready": {"values": ["guild", "bot"]},
    "shutdown": {"values": ["bot"]},
    "script load": {"values": ["script_name"]},
    "script error": {"values": ["script_name", "error", "line"]},

    "message": {"values": ["message", "channel", "author", "guild", "bot"]},
    "message receive": {"values": ["message", "channel", "author", "guild", "bot"]},
    "message in channel": {"values": ["message", "channel", "author", "guild", "bot"]},
    "message from guild": {"values": ["message", "channel", "author", "guild", "bot"]},
    "message edit": {"values": ["message", "channel", "author", "guild", "bot", "string"]},
    "message delete": {"values": ["message", "channel", "guild", "bot"]},
    "bulk message delete": {"values": ["messages", "bot"]},

    "reaction add": {"values": ["message", "emote", "user", "member", "channel", "guild", "bot"]},
    "reaction remove": {"values": ["message", "emote", "user", "channel", "guild", "bot"]},
    "reaction clear": {"values": ["message", "reactions", "channel", "guild", "bot"]},

    "slash command": {"values": ["interaction", "string", "user", "member", "channel", "guild", "bot"]},
    "slash command completion": {"values": ["interaction", "string", "user", "bot"]},
    "message command": {"values": ["interaction", "string", "user", "target_message", "channel", "guild", "bot"]},
    "user command": {"values": ["interaction", "string", "user", "target_user", "guild", "bot"]},

    "button click": {"values": ["interaction", "string", "user", "member", "channel", "guild", "message", "bot"]},
    "dropdown click": {"values": ["interaction", "string", "user", "member", "channel", "guild", "message", "selected values", "bot"]},
    "entity dropdown click": {"values": ["interaction", "string", "user", "member", "channel", "guild", "message", "selected entities", "bot"]},
    "modal receive": {"values": ["interaction", "string", "user", "member", "channel", "guild", "bot"]},

    "guild member join": {"values": ["member", "user", "guild", "bot"]},
    "guild member leave": {"values": ["member", "user", "guild", "bot"]},
    "guild member update": {"values": ["member", "user", "guild", "bot"]},
    "guild member ban": {"values": ["user", "member", "guild", "string", "bot"]},
    "guild member unban": {"values": ["user", "guild", "bot"]},
    "guild member timeout": {"values": ["member", "user", "guild", "timespan", "bot"]},
    "guild member role add": {"values": ["member", "user", "role", "guild", "bot"]},
    "guild member role remove": {"values": ["member", "user", "role", "guild", "bot"]},
    "guild boost": {"values": ["member", "user", "guild", "bot"]},
    "guild boost count update": {"values": ["guild", "count", "bot"]},

    "role create": {"values": ["role", "guild", "bot"]},
    "role delete": {"values": ["role", "guild", "bot"]},
    "role edit": {"values": ["role", "guild", "bot"]},

    "channel create": {"values": ["channel", "guild", "bot"]},
    "channel delete": {"values": ["channel", "guild", "bot"]},
    "channel edit": {"values": ["channel", "guild", "bot"]},
    "thread create": {"values": ["channel", "guild", "bot"]},
    "thread delete": {"values": ["channel", "guild", "bot"]},
    "thread update": {"values": ["channel", "guild", "bot"]},
    "thread member join": {"values": ["channel", "user", "member", "guild", "bot"]},
    "thread member leave": {"values": ["channel", "user", "member", "guild", "bot"]},

    "voice join": {"values": ["member", "user", "channel", "guild", "bot"]},
    "voice leave": {"values": ["member", "user", "channel", "guild", "bot"]},
    "voice move": {"values": ["member", "user", "before", "after", "guild", "bot"]},
    "voice mute": {"values": ["member", "user", "guild", "bot"]},
    "voice deafen": {"values": ["member", "user", "guild", "bot"]},
    "voice stream start": {"values": ["member", "user", "channel", "guild", "bot"]},
    "voice stream stop": {"values": ["member", "user", "channel", "guild", "bot"]},

    "guild emoji create": {"values": ["emote", "guild", "bot"]},
    "guild emoji delete": {"values": ["emote", "guild", "bot"]},
    "guild emoji edit": {"values": ["emote", "guild", "bot"]},
    "guild sticker create": {"values": ["sticker", "guild", "bot"]},
    "guild sticker delete": {"values": ["sticker", "guild", "bot"]},
    "guild sticker edit": {"values": ["sticker", "guild", "bot"]},
    "guild scheduled event create": {"values": ["scheduledevent", "guild", "bot"]},
    "guild scheduled event update": {"values": ["scheduledevent", "guild", "bot"]},
    "guild scheduled event delete": {"values": ["scheduledevent", "guild", "bot"]},
    "guild scheduled event user add": {"values": ["scheduledevent", "user", "guild", "bot"]},
    "guild scheduled event user remove": {"values": ["scheduledevent", "user", "guild", "bot"]},

    "guild update": {"values": ["guild", "bot"]},
    "invite create": {"values": ["invite", "guild", "bot"]},
    "invite delete": {"values": ["invite", "guild", "bot"]},
    "webhook update": {"values": ["channel", "guild", "bot"]},
    "poll vote add": {"values": ["message", "user", "channel", "guild", "bot"]},
    "poll vote remove": {"values": ["message", "user", "channel", "guild", "bot"]},
    "typing": {"values": ["channel", "user", "guild", "bot"]},
    "presence update": {"values": ["user", "guild", "bot"]},
    "interaction error": {"values": ["interaction", "bot"]},
}


class EventDefinitions:
    @staticmethod
    def get_values(event_type: str) -> list[str]:
        info = EVENT_DEFINITIONS.get(event_type)
        return info["values"] if info else []
