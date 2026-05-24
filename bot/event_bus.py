from __future__ import annotations
from language.runtime import Runtime, StopSignal, ReturnValue, Scope
from language.ast import EventHandler
from typing import Any, Optional
import asyncio
import re


EVENT_ALIASES: dict[str, list[str]] = {
    "message": ["message receive"],
    "message receive": ["message"],
    "message edit": [],
    "message delete": [],
    "bulk message delete": [],
    "reaction add": [],
    "reaction remove": [],
    "reaction clear": [],
    "bot ready": ["ready"],
    "guild ready": [],
    "shutdown": [],
    "slash command": [],
    "slash command completion": [],
    "message command": [],
    "user command": [],
    "button click": [],
    "dropdown click": [],
    "entity dropdown click": [],
    "modal receive": [],
    "guild member join": ["member join"],
    "guild member leave": ["member leave"],
    "guild member update": ["member update"],
    "guild member ban": ["member ban"],
    "guild member unban": ["member unban"],
    "guild member timeout": ["member timeout"],
    "guild member role add": ["member role add"],
    "guild member role remove": ["member role remove"],
    "guild boost": [],
    "guild boost count update": [],
    "role create": [],
    "role delete": [],
    "role edit": [],
    "channel create": [],
    "channel delete": [],
    "channel edit": [],
    "thread create": [],
    "thread delete": [],
    "thread update": [],
    "thread member join": [],
    "thread member leave": [],
    "voice join": [],
    "voice leave": [],
    "voice move": [],
    "voice mute": [],
    "voice deafen": [],
    "voice stream start": [],
    "voice stream stop": [],
    "guild emoji create": [],
    "guild emoji delete": [],
    "guild emoji edit": [],
    "guild emoji update": [],
    "guild sticker create": [],
    "guild sticker delete": [],
    "guild sticker edit": [],
    "guild sticker update": [],
    "guild scheduled event create": [],
    "guild scheduled event update": [],
    "guild scheduled event delete": [],
    "guild scheduled event user add": [],
    "guild scheduled event user remove": [],
    "guild update": [],
    "invite create": [],
    "invite delete": [],
    "webhook update": [],
    "poll vote add": [],
    "poll vote remove": [],
    "typing": [],
    "presence update": [],
    "interaction error": [],
    "script load": [],
    "script error": [],
}


class EventBus:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    async def fire(self, event_type: str, bot_name: str, values: dict[str, Any]) -> None:
        handlers = self._find_handlers(event_type, bot_name)
        if not handlers:
            return

        for handler in handlers:
            try:
                await self._execute_handler(handler, event_type, bot_name, values)
            except Exception as e:
                print(f"[EVENT] Error in handler for '{event_type}': {e}")

    def _find_handlers(self, event_type: str, bot_name: str) -> list[EventHandler]:
        matching: list[EventHandler] = []
        for handler in self.runtime.event_handlers:
            if self._event_matches(handler.event_type, event_type):
                if handler.bot_filter and handler.bot_filter != bot_name:
                    continue
                matching.append(handler)
        return matching

    def _event_matches(self, pattern: str, event_type: str) -> bool:
        if pattern == event_type:
            return True
        if event_type in EVENT_ALIASES and pattern in EVENT_ALIASES[event_type]:
            return True
        if pattern in EVENT_ALIASES and event_type in EVENT_ALIASES[pattern]:
            return True
        if re.match(pattern.replace("%", ".*").replace(" ", ".*"), event_type, re.IGNORECASE):
            return True
        return False

    async def _execute_handler(self, handler: EventHandler, event_type: str, bot_name: str, values: dict[str, Any]) -> None:
        ctx = self.runtime.event_context
        ctx.bot_name = bot_name
        old_values = dict(ctx.values)
        ctx.values.clear()
        for k, v in values.items():
            ctx.values[k] = v
        ctx.cancelled = False

        self.runtime.local_vars.clear()

        scope = Scope(self.runtime.global_scope)

        for key, val in values.items():
            scope.set(f"event-{key.replace(' ', '_')}", val)
            scope.set(f"event_{key.replace(' ', '_')}", val)

        scope.set("event-type", event_type)

        try:
            for stmt in handler.body:
                result = self.runtime.execute_effect_list([stmt], scope)
                if isinstance(result, dict) and "_wait" in result:
                    dur = result["_wait"]
                    if dur:
                        try:
                            from language.types import parse_timespan
                            seconds = parse_timespan(str(dur)) if isinstance(dur, str) else float(dur)
                            await asyncio.sleep(seconds)
                        except (ValueError, TypeError):
                            await asyncio.sleep(float(dur) if dur else 0)
                    self.runtime.local_vars.clear()
                if isinstance(result, StopSignal):
                    break
                if isinstance(result, ReturnValue):
                    break
        except Exception as e:
            if not hasattr(e, 'node'):
                from language.runtime import RuntimeError_
                e = RuntimeError_(f"Unhandled {type(e).__name__}: {e}")
            print(f"[EVENT ERROR] {e}")
            error_handlers = self._find_handlers("script error", bot_name)
            if error_handlers:
                for eh in error_handlers:
                    ctx.set("last_exception", str(e))
                    for stmt in eh.body:
                        self.runtime.execute_effect_list([stmt], scope)
        finally:
            ctx.values.update(old_values)

    async def fire_custom(self, event_name: str, data: Optional[dict] = None, bot_name: str = "") -> None:
        ctx = self.runtime.event_context
        ctx.set("custom_event_name", event_name)
        if data:
            for k, v in data.items():
                ctx.set(k, v)

        handlers = self.runtime.custom_event_handlers.get(event_name, [])
        for handler in handlers:
            if bot_name and handler.bot_filter and handler.bot_filter != bot_name:
                continue
            scope = Scope(self.runtime.global_scope)
            try:
                for stmt in handler.body:
                    self.runtime.execute_effect_list([stmt], scope)
            except Exception as e:
                print(f"[CUSTOM EVENT] Error: {e}")
