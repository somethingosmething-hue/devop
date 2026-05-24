from __future__ import annotations
from language.runtime import Runtime, Scope, RuntimeError_, StopSignal, ReturnValue, ContinueSignal, BreakSignal
from language.types import parse_color, parse_timespan, format_timespan, PERMISSION_NAMES
from typing import Any, Optional
import datetime
import random
import math
import re
import asyncio


def register_effects(runtime: Runtime) -> None:
    h = runtime.effect_handlers

    h["send"] = _effect_send
    h["send_console"] = _effect_send_console
    h["wait"] = _effect_wait
    h["stop"] = _effect_stop
    h["continue"] = _effect_continue
    h["break"] = _effect_break
    h["return"] = _effect_return
    h["reply"] = _effect_reply
    h["post"] = _effect_post
    h["broadcast"] = _effect_broadcast
    h["forward"] = _effect_forward
    h["crosspost"] = _effect_crosspost
    h["pin"] = _effect_pin
    h["unpin"] = _effect_unpin
    h["purge"] = _effect_purge
    h["delete"] = _effect_delete
    h["edit"] = _effect_edit
    h["edit_message"] = _effect_edit_message
    h["edit_button"] = _effect_edit_button
    h["edit_dropdown"] = _effect_edit_dropdown
    h["edit_components"] = _effect_edit_components

    h["kick"] = _effect_kick
    h["ban"] = _effect_ban
    h["unban"] = _effect_unban
    h["timeout"] = _effect_timeout
    h["timeout_until"] = _effect_timeout_until
    h["remove_timeout"] = _effect_remove_timeout
    h["move_member"] = _effect_move_member
    h["disconnect_member"] = _effect_disconnect_member
    h["mute_member"] = _effect_mute_member
    h["unmute_member"] = _effect_unmute_member
    h["deafen_member"] = _effect_deafen_member
    h["undeafen_member"] = _effect_undeafen_member
    h["add_role"] = _effect_add_role
    h["remove_role"] = _effect_remove_role
    h["set_nickname"] = _effect_set_nickname

    h["create_role"] = _effect_create_role
    h["create_invite"] = _effect_create_invite
    h["create_emote"] = _effect_create_emote
    h["create_sticker"] = _effect_create_sticker
    h["create_scheduled_event"] = _effect_create_scheduled_event
    h["create_poll"] = _effect_create_poll
    h["create_thread"] = _effect_create_thread
    h["create_forum_post"] = _effect_create_forum_post
    h["delete_channel"] = _effect_delete_channel

    h["make_embed"] = _effect_make_embed
    h["make_row"] = _effect_make_row
    h["make_container"] = _effect_make_container
    h["make_message"] = _effect_make_message
    h["post_last_embed"] = _effect_post_last_embed

    h["connect_voice"] = _effect_connect_voice
    h["disconnect_voice"] = _effect_disconnect_voice
    h["play_track"] = _effect_play_track
    h["stop_track"] = _effect_stop_track
    h["pause_track"] = _effect_pause_track
    h["resume_track"] = _effect_resume_track
    h["skip_track"] = _effect_skip_track
    h["load_audio"] = _effect_load_audio
    h["set_volume"] = _effect_set_volume
    h["set_repeat"] = _effect_set_repeat
    h["set_autoplay"] = _effect_set_autoplay
    h["set_audio_pitch"] = lambda r, a, k, b, s: _effect_set_audio_prop(r, a, {**k, "prop_name": "pitch"}, b, s)
    h["set_audio_speed"] = lambda r, a, k, b, s: _effect_set_audio_prop(r, a, {**k, "prop_name": "speed"}, b, s)
    h["set_audio_rotation"] = lambda r, a, k, b, s: _effect_set_audio_prop(r, a, {**k, "prop_name": "rotation"}, b, s)
    h["set_audio_mono"] = lambda r, a, k, b, s: _effect_set_audio_prop(r, a, {**k, "prop_name": "mono"}, b, s)
    h["set_audio_volume"] = lambda r, a, k, b, s: _effect_set_audio_prop(r, a, {**k, "prop_name": "volume"}, b, s)

    h["defer_interaction"] = _effect_defer_interaction
    h["show_modal"] = _effect_show_modal
    h["trigger_custom_event"] = _effect_trigger_custom_event
    h["set_presence"] = _effect_set_presence
    h["set_status"] = _effect_set_status
    h["shutdown_bot"] = _effect_shutdown_bot
    h["load_members"] = _effect_load_members
    h["send_typing"] = _effect_send_typing
    h["register_embed_template"] = _effect_register_embed_template
    h["register_webhook"] = _effect_register_webhook
    h["webhook_send"] = _effect_webhook_send
    h["webhook_delete"] = _effect_webhook_delete
    h["webhook_edit"] = _effect_webhook_edit
    h["set_cooldown"] = _effect_set_cooldown
    h["set_cooldown_message"] = _effect_set_cooldown_message
    h["set_cooldown_bypass"] = _effect_set_cooldown_bypass
    h["set_prefix"] = _effect_set_prefix
    h["update_command"] = _effect_update_command
    h["execute_command"] = _effect_execute
    h["edit_channel"] = _effect_edit_channel

    h["retrieve"] = _effect_retrieve
    h["retrieve_member"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_member", r, a, k, b, s)
    h["retrieve_message"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_message", r, a, k, b, s)
    h["retrieve_messages"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_messages", r, a, k, b, s)
    h["retrieve_user"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_user", r, a, k, b, s)
    h["retrieve_channel"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_channel", r, a, k, b, s)
    h["retrieve_bans"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_bans", r, a, k, b, s)
    h["retrieve_invites"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_invites", r, a, k, b, s)
    h["retrieve_webhooks"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_webhooks", r, a, k, b, s)
    h["retrieve_owner"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_owner", r, a, k, b, s)
    h["retrieve_audit_logs"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_audit_logs", r, a, k, b, s)
    h["retrieve_thread_members"] = lambda r, a, k, b, s: _effect_retrieve_dispatch("retrieve_thread_members", r, a, k, b, s)

    h["set_channel_topic"] = _effect_set_channel_topic
    h["set_channel_slowmode"] = _effect_set_channel_slowmode
    h["set_channel_nsfw"] = _effect_set_channel_nsfw
    h["set_channel_name"] = _effect_set_channel_name
    h["set_channel_position"] = _effect_set_channel_position
    h["set_channel_parent"] = _effect_set_channel_parent
    h["clone_channel"] = _effect_clone_channel
    h["add_reaction"] = _effect_add_reaction
    h["remove_reaction"] = _effect_remove_reaction
    h["clear_reactions"] = _effect_clear_reactions
    h["set_role_name"] = _effect_set_role_name
    h["set_role_color"] = _effect_set_role_color
    h["set_role_permissions"] = _effect_set_role_permissions
    h["set_role_hoist"] = _effect_set_role_hoist
    h["set_role_mentionable"] = _effect_set_role_mentionable
    h["delete_role"] = _effect_delete_role
    h["set_guild_name"] = _effect_set_guild_name
    h["set_guild_icon"] = _effect_set_guild_icon
    h["set_guild_banner"] = _effect_set_guild_banner
    h["set_guild_description"] = _effect_set_guild_description
    h["set_verification_level"] = _effect_set_verification_level
    h["set_guild_notification_level"] = _effect_set_guild_notification_level
    h["set_guild_nsfw_level"] = _effect_set_guild_nsfw_level
    h["set_afk_channel"] = _effect_set_afk_channel
    h["set_afk_timeout"] = _effect_set_afk_timeout
    h["set_system_channel"] = _effect_set_system_channel
    h["set_rules_channel"] = _effect_set_rules_channel
    h["set_public_updates_channel"] = _effect_set_public_updates_channel
    h["modify_welcome_screen"] = _effect_modify_welcome_screen
    h["add_reaction_role"] = _effect_add_reaction_role
    h["delete_invite"] = _effect_delete_invite
    h["delete_scheduled_event"] = _effect_delete_scheduled_event
    h["delete_sticker"] = _effect_delete_sticker


def _resolve_obj(runtime: Runtime, expr: Any, scope: Scope) -> Any:
    if isinstance(expr, str):
        val = runtime.global_scope.get(expr)
        if val is None:
            val = runtime.local_vars.get(expr)
        return val
    if hasattr(expr, 'line') or hasattr(expr, 'effect_type'):
        return runtime.evaluate(expr, scope)
    return expr


def _schedule(coro) -> None:
    try:
        asyncio.get_event_loop().create_task(coro)
    except (RuntimeError, Exception):
        pass


def _store_result(runtime: Runtime, store_in: Any, value: Any, scope: Scope) -> None:
    if not store_in:
        return
    name = store_in if isinstance(store_in, str) else (getattr(store_in, 'value', None) or str(store_in))
    if name.startswith("_"):
        runtime.local_vars[name] = value
    else:
        scope.set(name, value)
        runtime.global_scope.set(name, value)


def _resolve_channel(obj: Any) -> Any:
    if hasattr(obj, 'send'):
        return obj
    if isinstance(obj, str):
        return None
    return obj


def _resolve_guild(obj: Any) -> Any:
    if hasattr(obj, 'members'):
        return obj
    return None


def _effect_send(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    content = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    target = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    store_in = kwargs.get("store_in")

    if isinstance(content, dict) and content.get("type") == "message":
        data = content.get("data", {})
        content_str = data.get("content", "")
        embeds = data.get("embeds", [])
        components_data = data.get("components", [])
        view = _build_view(components_data)
        result = {"type": "send", "content": content_str, "target": str(target) if target else ""}
        if target is not None and hasattr(target, 'send'):
            send_kwargs = {}
            if content_str:
                send_kwargs["content"] = content_str
            if embeds:
                if len(embeds) == 1:
                    send_kwargs["embed"] = embeds[0]
                else:
                    send_kwargs["embeds"] = embeds
            if view:
                send_kwargs["view"] = view
            _schedule(target.send(**send_kwargs))
        elif target is not None and hasattr(target, 'reply'):
            _schedule(target.reply(content_str))
    else:
        content_str = str(content) if content else ""
        result = {"type": "send", "content": content_str, "target": str(target) if target else ""}
        view = None
        last_row = runtime.local_vars.get("last_row")
        if last_row:
            view = _build_view([last_row] if isinstance(last_row, dict) else last_row)
        if target is not None and hasattr(target, 'send'):
            send_kwargs = {"content": content_str}
            if view:
                send_kwargs["view"] = view
            _schedule(target.send(**send_kwargs))
        elif target is not None and hasattr(target, 'reply'):
            _schedule(target.reply(content_str))

    _store_result(runtime, store_in, result, scope)
    print(f"[SEND] {content_str[:80]} -> {target}")
    return result


def _effect_send_console(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    content = str(_resolve_obj(runtime, args[0], scope) or "") if args else ""
    print(content)
    return content


def _effect_wait(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    dur = _resolve_obj(runtime, args[0], scope) if args else None
    return {"_wait": dur}


def _effect_stop(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    from language.runtime import StopSignal
    return StopSignal()


def _effect_continue(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    from language.runtime import ContinueSignal
    return ContinueSignal()


def _effect_break(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    from language.runtime import BreakSignal
    return BreakSignal()


def _effect_return(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    from language.runtime import ReturnValue
    val = _resolve_obj(runtime, args[0], scope) if args else None
    return ReturnValue(val)


def _build_view(components_data: list) -> Any:
    import discord
    if not components_data:
        return None
    view = discord.ui.View(timeout=None)
    for row_data in components_data:
        if isinstance(row_data, dict):
            row_type = row_data.get("type", "")
            if row_type == "component_row":
                for comp in row_data.get("components", []):
                    if isinstance(comp, dict):
                        if comp.get("type") == "button":
                            style_map = {1: discord.ButtonStyle.primary, 2: discord.ButtonStyle.secondary,
                                           3: discord.ButtonStyle.success, 4: discord.ButtonStyle.danger,
                                           5: discord.ButtonStyle.link}
                            style = style_map.get(comp.get("style", 1), discord.ButtonStyle.primary)
                            custom_id = comp.get("id")
                            label = comp.get("label", "")
                            emoji = comp.get("emoji")
                            url = comp.get("url")
                            if style == discord.ButtonStyle.link:
                                view.add_item(discord.ui.Button(style=style, label=label, url=url, emoji=emoji))
                            else:
                                view.add_item(discord.ui.Button(style=style, label=label, custom_id=custom_id, emoji=emoji))
                        elif comp.get("type") in ("dropdown", "select"):
                            options = []
                            for opt in comp.get("options", []):
                                if isinstance(opt, dict):
                                    options.append(discord.SelectOption(
                                        label=opt.get("label", ""),
                                        value=opt.get("value", ""),
                                        description=opt.get("description"),
                                        emoji=opt.get("emoji"),
                                    ))
                            if options:
                                view.add_item(discord.ui.Select(
                                    custom_id=comp.get("id", ""),
                                    placeholder=comp.get("placeholder"),
                                    min_values=comp.get("min_values", 1),
                                    max_values=comp.get("max_values", 1),
                                    options=options,
                                ))
                            else:
                                view.add_item(discord.ui.Select(
                                    custom_id=comp.get("id", ""),
                                    placeholder=comp.get("placeholder"),
                                    min_values=comp.get("min_values", 1),
                                    max_values=comp.get("max_values", 1),
                                ))
            elif row_type == "container":
                for content_item in row_data.get("content", []):
                    ctype = content_item.get("type", "")
                    if ctype == "separator":
                        view.add_item(discord.ui.Button(
                            style=discord.ButtonStyle.secondary,
                            label="──────────",
                            custom_id=f"separator_{id(content_item)}",
                            disabled=True,
                        ))
                    elif ctype == "media_gallery":
                        urls = content_item.get("urls", [])
                        for url in urls[:4]:
                            view.add_item(discord.ui.Button(
                                style=discord.ButtonStyle.link,
                                label="View Media",
                                url=str(url),
                            ))
                    elif ctype == "section":
                        text = content_item.get("text", "")
                        accessory = content_item.get("accessory")
                        if text:
                            view.add_item(discord.ui.Button(
                                style=discord.ButtonStyle.secondary,
                                label=str(text)[:80],
                                custom_id=f"section_{id(content_item)}",
                                disabled=True,
                            ))
                        if accessory and isinstance(accessory, dict):
                            if accessory.get("type") == "button":
                                view.add_item(discord.ui.Button(
                                    style=_parse_button_style(accessory.get("style", "secondary")),
                                    label=accessory.get("label", ""),
                                    custom_id=accessory.get("id", ""),
                                ))
                    elif ctype == "component_row":
                        for comp in content_item.get("components", []):
                            if isinstance(comp, dict) and comp.get("type") == "button":
                                view.add_item(discord.ui.Button(
                                    style=_parse_button_style(comp.get("style", "secondary")),
                                    label=comp.get("label", ""),
                                    custom_id=comp.get("id", ""),
                                    emoji=comp.get("emoji"),
                                ))
    return view if view.children else None


def _send_with_view(target: Any, content: str = None, embed=None, view=None) -> None:
    kwargs = {}
    if content:
        kwargs["content"] = content
    if embed:
        kwargs["embed"] = embed
    if view:
        kwargs["view"] = view
    _schedule(target.send(**kwargs))


def _effect_reply(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    content = _resolve_obj(runtime, args[0], scope) if args else None
    hidden = kwargs.get("hidden", False)
    store_in = kwargs.get("store_in")
    interaction = runtime.event_context.get("interaction")
    message = runtime.event_context.get("message")

    content_str = str(content) if content else ""
    view = None
    if isinstance(content, dict) and content.get("type") == "message":
        data = content.get("data", {})
        content_str = data.get("content", "")
        embeds_data = data.get("embeds", [])
        components_data = data.get("components", [])
        if components_data:
            view = _build_view(components_data)
    else:
        last_row = runtime.local_vars.get("last_row")
        if last_row:
            view = _build_view([last_row] if isinstance(last_row, dict) else last_row)

    if interaction is not None and hasattr(interaction, 'response') and not interaction.response.is_done():
        try:
            kwargs = {"content": content_str, "ephemeral": hidden}
            if view:
                kwargs["view"] = view
            _schedule(interaction.response.send_message(**kwargs))
        except Exception:
            _schedule(interaction.followup.send(content_str, ephemeral=hidden))
    elif message is not None and hasattr(message, 'reply'):
        if view:
            _schedule(message.reply(content_str, view=view))
        else:
            _schedule(message.reply(content_str))

    result = {"type": "reply", "content": content_str, "hidden": hidden}
    _store_result(runtime, store_in, result, scope)
    return result


def _effect_post(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    content = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    target = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    store_in = kwargs.get("store_in")

    if content is not None and target is not None and hasattr(target, 'send'):
        if isinstance(content, dict) and content.get("type") == "embed":
            import discord
            emb = discord.Embed.from_dict(content.get("data", {}))
            _schedule(target.send(embed=emb))
        elif isinstance(content, dict) and content.get("type") == "message":
            data = content.get("data", {})
            components_data = data.get("components", [])
            view = _build_view(components_data)
            send_kwargs = {}
            if data.get("content"):
                send_kwargs["content"] = data["content"]
            if data.get("embeds"):
                embeds_list = data["embeds"]
                if len(embeds_list) == 1:
                    send_kwargs["embed"] = embeds_list[0]
                else:
                    send_kwargs["embeds"] = embeds_list
            if view:
                send_kwargs["view"] = view
            _schedule(target.send(**send_kwargs))
        else:
            _schedule(target.send(str(content)))

    result = {"type": "post", "content": str(content) if content else "", "target": str(target) if target else ""}
    _store_result(runtime, store_in, result, scope)
    return result


def _effect_broadcast(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    content = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    target = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if target is not None and hasattr(target, 'text_channels'):
        for ch in target.text_channels:
            try:
                _schedule(ch.send(content))
            except Exception:
                pass
    print(f"[BROADCAST] {content[:60]} -> {target}")
    return content


def _effect_forward(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    target = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if msg is not None and target is not None and hasattr(target, 'send'):
        _schedule(target.send(msg))
    print(f"[FORWARD] {msg} -> {target}")
    return None


def _effect_crosspost(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if args else None
    if msg is not None and hasattr(msg, 'publish'):
        _schedule(msg.publish())
    print(f"[CROSSPOST] {msg}")
    return None


def _effect_pin(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if args else None
    if msg is not None and hasattr(msg, 'pin'):
        _schedule(msg.pin())
    print(f"[PIN] {msg}")
    return None


def _effect_unpin(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if args else None
    if msg is not None and hasattr(msg, 'unpin'):
        _schedule(msg.unpin())
    print(f"[UNPIN] {msg}")
    return None


def _effect_purge(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    count = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else 0
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 0
    if channel is not None and hasattr(channel, 'purge') and count > 0:
        _schedule(channel.purge(limit=count))
    print(f"[PURGE] {count} messages")
    return None


def _effect_delete(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    target = _resolve_obj(runtime, args[0], scope) if args else None
    if target is not None:
        if hasattr(target, 'delete'):
            _schedule(target.delete())
        elif hasattr(target, 'kick'):
            _schedule(target.kick())
    print(f"[DELETE] {target}")
    return None


def _effect_edit(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    target = _resolve_obj(runtime, args[0], scope) if args else None
    content = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if target is not None and content is not None:
        if hasattr(target, 'edit'):
            _schedule(target.edit(content=str(content)))
    print(f"[EDIT] {target}")
    return None


def _effect_edit_message(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    content = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if msg is not None and hasattr(msg, 'edit'):
        if isinstance(content, dict) and content.get("type") == "embed":
            import discord
            emb = discord.Embed.from_dict(content.get("data", {}))
            _schedule(msg.edit(embed=emb))
        else:
            _schedule(msg.edit(content=str(content) if content else ""))
    print(f"[EDIT MESSAGE] {msg}")
    return None


def _effect_edit_button(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    custom_id = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    label = str(_resolve_obj(runtime, kwargs.get("label"), scope) or "") if kwargs.get("label") else None
    style = str(_resolve_obj(runtime, kwargs.get("style"), scope) or "") if kwargs.get("style") else None
    disabled = _resolve_obj(runtime, kwargs.get("disabled"), scope) if kwargs.get("disabled") else None
    emoji = str(_resolve_obj(runtime, kwargs.get("emoji"), scope) or "") if kwargs.get("emoji") else None

    if msg is not None and hasattr(msg, 'edit') and custom_id:
        import discord
        new_btn = discord.ui.Button(
            label=label or "",
            custom_id=custom_id,
            style=_parse_button_style(style) if style else discord.ButtonStyle.secondary,
            disabled=bool(disabled) if disabled is not None else False,
            emoji=emoji if emoji else None,
        )
        _schedule(_edit_component_on_message(msg, custom_id, new_btn))

    print(f"[EDIT BUTTON] {custom_id} {label}")
    return None


def _effect_edit_dropdown(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    custom_id = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    placeholder = str(_resolve_obj(runtime, kwargs.get("placeholder"), scope) or "") if kwargs.get("placeholder") else None
    disabled = _resolve_obj(runtime, kwargs.get("disabled"), scope) if kwargs.get("disabled") else None
    min_vals = int(_resolve_obj(runtime, kwargs.get("min_values"), scope) or 0) if kwargs.get("min_values") else None
    max_vals = int(_resolve_obj(runtime, kwargs.get("max_values"), scope) or 0) if kwargs.get("max_values") else None

    if msg is not None and hasattr(msg, 'edit') and custom_id:
        import discord
        new_dd = discord.ui.Select(
            custom_id=custom_id,
            placeholder=placeholder or "",
            disabled=bool(disabled) if disabled is not None else False,
            min_values=min_vals or 0,
            max_values=max_vals or 1,
        )
        _schedule(_edit_component_on_message(msg, custom_id, new_dd))

    print(f"[EDIT DROPDOWN] {custom_id}")
    return None


def _edit_component_on_message(msg, custom_id: str, new_component) -> None:
    if not hasattr(msg, 'components') or not msg.components:
        return None
    new_components = []
    for row in msg.components:
        new_row_components = []
        for comp in row.children if hasattr(row, 'children') else []:
            if hasattr(comp, 'custom_id') and comp.custom_id == custom_id:
                new_row_components.append(new_component)
            else:
                new_row_components.append(comp)
        new_components.append(new_row_components)

    import discord
    discord_components = []
    for row_comps in new_components:
        discord_components.append(discord.ui.ActionRow(*row_comps))
    coro = msg.edit(view=discord.ui.View(*discord_components))
    return coro


def _parse_button_style(style: str) -> Any:
    import discord
    style_map = {
        "primary": discord.ButtonStyle.primary,
        "secondary": discord.ButtonStyle.secondary,
        "success": discord.ButtonStyle.success,
        "danger": discord.ButtonStyle.danger,
        "link": discord.ButtonStyle.link,
        "blurple": discord.ButtonStyle.primary,
        "grey": discord.ButtonStyle.secondary,
        "green": discord.ButtonStyle.success,
        "red": discord.ButtonStyle.danger,
        "gray": discord.ButtonStyle.secondary,
    }
    return style_map.get(style.lower(), discord.ButtonStyle.secondary)


def _effect_edit_components(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    new_comps = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if msg is not None and hasattr(msg, 'edit') and new_comps is not None:
        import discord
        if isinstance(new_comps, dict) and new_comps.get("type") == "component_row":
            rows = [new_comps]
        elif isinstance(new_comps, list):
            rows = new_comps
        else:
            rows = [new_comps]

        view = discord.ui.View()
        for row in rows:
            if isinstance(row, dict) and row.get("type") == "component_row":
                children = row.get("components", [])
                discord_children = []
                for child in children:
                    if isinstance(child, dict) and child.get("type") == "button":
                        discord_children.append(discord.ui.Button(
                            label=child.get("label", ""),
                            custom_id=child.get("id", ""),
                            style=_parse_button_style(child.get("style", "secondary")),
                            disabled=child.get("disabled", False),
                        ))
                    elif isinstance(child, dict) and child.get("type") == "dropdown":
                        discord_children.append(discord.ui.Select(
                            custom_id=child.get("id", ""),
                            placeholder=child.get("placeholder", ""),
                            disabled=child.get("disabled", False),
                            options=[],
                        ))
                if discord_children:
                    view.add_item(discord.ui.ActionRow(*discord_children))
        _schedule(msg.edit(view=view))
    print(f"[EDIT COMPONENTS]")
    return None


def _effect_kick(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    reason = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else None
    if member is not None and hasattr(member, 'kick'):
        _schedule(member.kick(reason=reason))
    print(f"[KICK] {member} reason={reason}")
    return None


def _effect_ban(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    reason = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else None
    delete_dur = _resolve_obj(runtime, args[2], scope) if len(args) > 2 else None
    delete_days = 0
    if delete_dur is not None:
        try:
            delete_days = int(parse_timespan(str(delete_dur)) / 86400) if isinstance(delete_dur, str) else int(delete_dur)
        except (ValueError, TypeError):
            delete_days = 0
    if member is not None and hasattr(member, 'ban'):
        _schedule(member.ban(reason=reason, delete_message_days=delete_days))
    print(f"[BAN] {member} reason={reason}")
    return None


def _effect_unban(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    user = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    guild = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if guild is not None and user is not None and hasattr(guild, 'unban'):
        _schedule(guild.unban(user))
    print(f"[UNBAN] {user} from {guild}")
    return None


def _effect_timeout(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    duration = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    reason = str(_resolve_obj(runtime, args[2], scope) or "") if len(args) > 2 else None
    if member is not None and hasattr(member, 'timeout'):
        try:
            seconds = parse_timespan(str(duration)) if isinstance(duration, str) else (float(duration) if duration else 0)
            until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
            _schedule(member.timeout(until, reason=reason))
        except Exception:
            pass
    print(f"[TIMEOUT] {member} for {duration}")
    return None


def _effect_timeout_until(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    until = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    reason = str(_resolve_obj(runtime, args[2], scope) or "") if len(args) > 2 else None
    if member is not None and hasattr(member, 'timeout'):
        _schedule(member.timeout(until, reason=reason))
    print(f"[TIMEOUT UNTIL] {member} until {until}")
    return None


def _effect_remove_timeout(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if args else None
    if member is not None and hasattr(member, 'timeout'):
        _schedule(member.timeout(None))
    print(f"[REMOVE TIMEOUT] {member}")
    return None


def _effect_move_member(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if member is not None and hasattr(member, 'move_to') and channel is not None:
        _schedule(member.move_to(channel))
    print(f"[MOVE] {member} -> {channel}")
    return None


def _effect_disconnect_member(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if args else None
    if member is not None and hasattr(member, 'move_to'):
        _schedule(member.move_to(None))
    print(f"[DISCONNECT] {member}")
    return None


def _effect_mute_member(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if args else None
    if member is not None and hasattr(member, 'edit'):
        _schedule(member.edit(mute=True))
    print(f"[MUTE] {member}")
    return None


def _effect_unmute_member(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if args else None
    if member is not None and hasattr(member, 'edit'):
        _schedule(member.edit(mute=False))
    print(f"[UNMUTE] {member}")
    return None


def _effect_deafen_member(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if args else None
    if member is not None and hasattr(member, 'edit'):
        _schedule(member.edit(deafen=True))
    print(f"[DEAFEN] {member}")
    return None


def _effect_undeafen_member(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if args else None
    if member is not None and hasattr(member, 'edit'):
        _schedule(member.edit(deafen=False))
    print(f"[UNDEAFEN] {member}")
    return None


def _effect_add_role(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    member = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if member is not None and role is not None and hasattr(member, 'add_roles'):
        _schedule(member.add_roles(role))
    print(f"[ADD ROLE] {role} -> {member}")
    return None


def _effect_remove_role(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    member = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if member is not None and role is not None and hasattr(member, 'remove_roles'):
        _schedule(member.remove_roles(role))
    print(f"[REMOVE ROLE] {role} from {member}")
    return None


def _effect_set_nickname(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    member = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    nick = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else None
    if member is not None and hasattr(member, 'edit'):
        _schedule(member.edit(nick=nick))
    print(f"[SET NICKNAME] {member} -> {nick}")
    return None


def _effect_create_role(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "new role") if len(args) > 0 else "new role"
    guild = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    store_in = kwargs.get("store_in")
    result = {"type": "role", "name": name}
    if guild is not None and hasattr(guild, 'create_role'):
        _schedule(guild.create_role(name=name))
    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE ROLE] {name}")
    return result


def _effect_create_invite(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    channel = _resolve_obj(runtime, args[0], scope) if args else None
    max_uses = _resolve_obj(runtime, kwargs.get("max_uses"), scope) if kwargs.get("max_uses") else None
    max_age = _resolve_obj(runtime, kwargs.get("max_age"), scope) if kwargs.get("max_age") else None
    store_in = kwargs.get("store_in")
    result = {"type": "invite", "channel": str(channel) if channel else ""}

    try:
        max_uses = int(max_uses) if max_uses is not None else 0
    except (TypeError, ValueError):
        max_uses = 0
    try:
        max_age = int(parse_timespan(str(max_age))) if isinstance(max_age, str) else (int(max_age) if max_age else 86400)
    except (TypeError, ValueError):
        max_age = 86400

    if channel is not None and hasattr(channel, 'create_invite'):
        _schedule(channel.create_invite(max_uses=max_uses, max_age=max_age))

    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE INVITE] for {channel}")
    return result


def _effect_create_emote(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    image_path = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    guild = _resolve_obj(runtime, args[2], scope) if len(args) > 2 else None
    store_in = kwargs.get("store_in")
    result = {"type": "emote", "name": name}
    if guild is not None and hasattr(guild, 'create_custom_emoji') and name and image_path:
        try:
            import discord
            with open(image_path, "rb") as f:
                image_data = f.read()
            _schedule(guild.create_custom_emoji(name=name, image=image_data))
        except Exception:
            pass
    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE EMOTE] {name}")
    return result


def _effect_create_sticker(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    description = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    image_path = str(_resolve_obj(runtime, args[2], scope) or "") if len(args) > 2 else ""
    emoji = str(_resolve_obj(runtime, args[3], scope) or "👍") if len(args) > 3 else "👍"
    guild = _resolve_obj(runtime, args[4], scope) if len(args) > 4 else None
    store_in = kwargs.get("store_in")
    result = {"type": "sticker", "name": name}
    if guild is not None and hasattr(guild, 'create_sticker') and name and image_path:
        try:
            import discord
            with open(image_path, "rb") as f:
                image_data = f.read()
            _schedule(guild.create_sticker(name=name, description=description, file=discord.File(image_path), emoji=emoji))
        except Exception:
            pass
    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE STICKER] {name}")
    return result


def _effect_create_scheduled_event(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    guild = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else runtime.event_context.get("guild")
    start = _resolve_obj(runtime, kwargs.get("start"), scope) if kwargs.get("start") else None
    end = _resolve_obj(runtime, kwargs.get("end"), scope) if kwargs.get("end") else None
    description = str(_resolve_obj(runtime, kwargs.get("description"), scope) or "") if kwargs.get("description") else ""
    channel = _resolve_obj(runtime, kwargs.get("channel"), scope) if kwargs.get("channel") else None
    location = str(_resolve_obj(runtime, kwargs.get("location"), scope) or "") if kwargs.get("location") else None
    privacy = str(kwargs.get("privacy", "guild_only") or "guild_only").lower()
    entity_type = str(kwargs.get("type", "external") or "external").lower()
    store_in = kwargs.get("store_in")
    result = {"type": "scheduled_event", "name": name}

    if guild and hasattr(guild, 'create_scheduled_event') and name and (start):
        import discord
        import datetime as dt
        try:
            start_dt = start if isinstance(start, dt.datetime) else dt.datetime.fromisoformat(str(start))
            end_dt = end if isinstance(end, dt.datetime) else (start_dt + dt.timedelta(hours=1) if end is None else dt.datetime.fromisoformat(str(end)))

            entity_map = {
                "stage": discord.EntityType.stage_instance,
                "voice": discord.EntityType.voice,
                "external": discord.EntityType.external,
            }
            privacy_map = {
                "guild_only": discord.PrivacyLevel.guild_only,
                "invite_only": discord.PrivacyLevel.invite_only,
            }

            kwargs_event = {
                "name": name,
                "description": description or None,
                "start_time": start_dt,
                "end_time": end_dt if entity_type == "external" else None,
                "privacy_level": privacy_map.get(privacy, discord.PrivacyLevel.guild_only),
                "entity_type": entity_map.get(entity_type, discord.EntityType.external),
            }
            if channel and entity_type != "external":
                kwargs_event["channel"] = channel
            if location and entity_type == "external":
                kwargs_event["location"] = location

            _schedule(guild.create_scheduled_event(**kwargs_event))
            result["created"] = True
        except Exception as e:
            print(f"[CREATE SCHEDULED EVENT ERROR] {e}")
            result["error"] = str(e)

    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE SCHEDULED EVENT] {name}")
    return result


def _effect_create_poll(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    question = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    options_raw = kwargs.get("options", [])
    duration_raw = kwargs.get("duration")
    store_in = kwargs.get("store_in")

    result = {"type": "poll", "question": question, "created": False}

    if channel and hasattr(channel, 'send') and question and options_raw:
        import discord
        try:
            answers = []
            for opt in options_raw:
                text = str(_resolve_obj(runtime, opt, scope) or "") if not isinstance(opt, str) else opt
                if text:
                    answers.append(discord.PollAnswer(text=text))

            duration_val = _resolve_obj(runtime, duration_raw, scope) if duration_raw else None
            duration_hours = 1
            if duration_val is not None:
                try:
                    duration_hours = float(duration_val)
                except (TypeError, ValueError):
                    from language.types import parse_timespan
                    duration_hours = parse_timespan(str(duration_val)) / 3600
            duration_hours = max(1, min(168, duration_hours))

            if hasattr(discord, 'Poll') and answers:
                poll = discord.Poll(
                    question=question,
                    answers=answers,
                    duration=duration_hours,
                )
                _schedule(channel.send(poll=poll))
                result["created"] = True
            else:
                lines = [f"**{question}**"]
                emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
                for i, opt in enumerate(options_raw):
                    text = str(_resolve_obj(runtime, opt, scope) or "") if not isinstance(opt, str) else opt
                    emoji = emojis[i] if i < len(emojis) else "✅"
                    lines.append(f"{emoji} {text}")
                _schedule(channel.send("\n".join(lines)))
                result["created"] = True
        except Exception as e:
            print(f"[CREATE POLL ERROR] {e}")
            result["error"] = str(e)

    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE POLL] {question[:50]}")
    return result


def _effect_create_thread(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    store_in = kwargs.get("store_in")
    result = {"type": "thread", "name": name}
    if channel is not None and hasattr(channel, 'create_thread'):
        _schedule(channel.create_thread(name=name))
    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE THREAD] {name}")
    return result


def _effect_create_forum_post(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    content = str(_resolve_obj(runtime, kwargs.get("content"), scope) or "") if kwargs.get("content") else ""
    store_in = kwargs.get("store_in")
    result = {"type": "forum_post", "name": name}
    if channel is not None and hasattr(channel, 'create_thread'):
        _schedule(channel.create_thread(name=name, content=content))
    _store_result(runtime, store_in, result, scope)
    print(f"[CREATE FORUM POST] {name}")
    return result


def _effect_delete_channel(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    channel = _resolve_obj(runtime, args[0], scope) if args else None
    if channel is not None and hasattr(channel, 'delete'):
        _schedule(channel.delete())
    print(f"[DELETE CHANNEL] {channel}")
    return None


def _effect_make_embed(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    embed = runtime._handle_embed_builder(args, kwargs, body, scope)
    runtime.local_vars["last_embed"] = embed
    return embed


def _effect_make_row(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    components = []
    for stmt in body or []:
        if hasattr(stmt, 'effect_type') and stmt.effect_type == "row_add_component":
            comp = _resolve_obj(runtime, stmt.arguments[0], scope)
            if comp:
                components.append(comp)
    store_in = kwargs.get("store_in")
    result = {"type": "component_row", "components": components}
    _store_result(runtime, store_in, result, scope)
    runtime.local_vars["last_row"] = result
    return result


def _effect_make_container(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    container_id = kwargs.get("id")
    result = {"type": "container", "id": container_id}
    store_in = kwargs.get("store_in")
    _store_result(runtime, store_in, result, scope)
    print(f"[MAKE CONTAINER] id={container_id}")
    return result


def _effect_make_message(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    content = None
    embeds = []
    components = []
    for stmt in body or []:
        if hasattr(stmt, 'effect_type'):
            if stmt.effect_type == "message_set_content":
                content = _resolve_obj(runtime, stmt.arguments[0], scope)
            elif stmt.effect_type == "message_add_embed":
                emb = _resolve_obj(runtime, stmt.arguments[0], scope)
                if emb:
                    embeds.append(emb)
            elif stmt.effect_type == "message_add_row":
                row = _resolve_obj(runtime, stmt.arguments[0], scope)
                if row:
                    components.append(row)
    store_in = kwargs.get("store_in")
    silent = kwargs.get("silent", False)
    result = {
        "type": "message",
        "data": {
            "content": str(content) if content else "",
            "embeds": embeds,
            "components": components,
            "silent": silent,
        },
    }
    _store_result(runtime, store_in, result, scope)
    return result


def _effect_post_last_embed(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    embed = runtime.local_vars.get("last_embed")
    target = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("channel")
    view = None
    component_row = kwargs.get("component_row")
    if component_row:
        row = _resolve_obj(runtime, component_row, scope)
    else:
        row = runtime.local_vars.get("last_row")
    if row:
        view = _build_view([row] if isinstance(row, dict) else row)
    if embed is not None and target is not None and hasattr(target, 'send'):
        if view:
            _schedule(target.send(embed=embed, view=view))
        else:
            _schedule(target.send(embed=embed))
    print(f"[POST LAST EMBED] -> {target}")
    return embed


def _effect_connect_voice(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    channel = _resolve_obj(runtime, args[0], scope) if args else None
    if channel is not None and hasattr(channel, 'connect'):
        try:
            _schedule(channel.connect())
            guild_id = getattr(channel, 'guild', None) and channel.guild.id
            if guild_id:
                audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
                if audio:
                    audio.connect(guild_id, channel)
            print(f"[CONNECT VOICE] -> {channel}")
        except Exception as e:
            print(f"[CONNECT VOICE ERROR] {e}")
    return None


def _effect_disconnect_voice(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if args else None
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio:
            audio.disconnect(getattr(guild, 'id', 0))
    print(f"[DISCONNECT VOICE]")
    return None


def _effect_play_track(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    track = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    guild = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else runtime.event_context.get("guild")
    store_in = kwargs.get("store_in")

    result = None
    if guild is not None and track is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        guild_id = getattr(guild, 'id', 0)

        if audio:
            audio.play(guild_id, track)
            result = track
            print(f"[PLAY TRACK] {getattr(track, 'title', str(track)[:50])}")

    _store_result(runtime, store_in, result, scope)
    return result


def _effect_stop_track(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, kwargs.get("guild"), scope) if kwargs.get("guild") else runtime.event_context.get("guild")
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio:
            audio.stop(getattr(guild, 'id', 0))
    print(f"[STOP TRACK]")
    return None


def _effect_pause_track(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, kwargs.get("guild"), scope) if kwargs.get("guild") else runtime.event_context.get("guild")
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio:
            audio.pause(getattr(guild, 'id', 0))
    print(f"[PAUSE TRACK]")
    return None


def _effect_resume_track(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, kwargs.get("guild"), scope) if kwargs.get("guild") else runtime.event_context.get("guild")
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio:
            audio.resume(getattr(guild, 'id', 0))
    print(f"[RESUME TRACK]")
    return None


def _effect_skip_track(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, kwargs.get("guild"), scope) if kwargs.get("guild") else runtime.event_context.get("guild")
    store_in = kwargs.get("store_in")
    result = None
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio:
            guild_id = getattr(guild, 'id', 0)
            result = audio.skip(guild_id)
    _store_result(runtime, store_in, result, scope)
    print(f"[SKIP TRACK]")
    return result


def _effect_load_audio(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    query = str(_resolve_obj(runtime, args[0], scope) or "") if args else ""
    store_in = kwargs.get("store_in")
    from bot.audio_manager import AudioTrack, AudioPlaylist
    result = None
    if query.startswith("http"):
        track = AudioTrack(title=f"Track: {query[:50]}", url=query)
        for stmt in body or []:
            if hasattr(stmt, 'effect_type') and stmt.effect_type == "audio_track_load":
                sc = Scope(scope)
                sc.set("loaded track", track)
                runtime.execute_effect_list(stmt.body or [], sc)
                result = track
    else:
        playlist = AudioPlaylist(name=f"Search: {query}")
        for stmt in body or []:
            if hasattr(stmt, 'effect_type') and stmt.effect_type == "audio_no_matches":
                runtime.execute_effect_list(stmt.body or [], scope)
                result = None
            elif hasattr(stmt, 'effect_type') and stmt.effect_type == "audio_load_error":
                runtime.execute_effect_list(stmt.body or [], scope)
    _store_result(runtime, store_in, result, scope)
    return result


def _effect_set_volume(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    vol = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else 100
    try:
        vol = float(vol)
    except (TypeError, ValueError):
        vol = 100
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio is not None:
            guild_id = getattr(guild, 'id', 0)
            audio.set_volume(guild_id, vol)
    print(f"[SET VOLUME] {vol}")
    return vol


def _effect_set_repeat(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    repeat = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else False
    if isinstance(repeat, str):
        repeat = repeat.lower() in ("true", "yes", "1")
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio is not None:
            audio.set_repeat(getattr(guild, 'id', 0), bool(repeat))
    print(f"[SET REPEAT] {repeat}")
    return repeat


def _effect_set_autoplay(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    auto = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else False
    if isinstance(auto, str):
        auto = auto.lower() in ("true", "yes", "1")
    if guild is not None:
        audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
        if audio is not None:
            audio.set_autoplay(getattr(guild, 'id', 0), bool(auto))
    print(f"[SET AUTOPLAY] {auto}")
    return auto


def _effect_set_audio_prop(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else runtime.event_context.get("guild")
    val = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else 0
    try:
        val = float(val)
    except (TypeError, ValueError):
        val = 0
    prop_name = kwargs.get("prop_name", "")
    audio = runtime.audio_manager if hasattr(runtime, 'audio_manager') else None
    if audio and guild:
        guild_id = getattr(guild, 'id', 0)
        if prop_name == "pitch":
            audio.set_pitch(guild_id, val)
        elif prop_name == "speed":
            audio.set_speed(guild_id, val)
        elif prop_name == "rotation":
            audio.set_rotation(guild_id, val)
        elif prop_name == "mono":
            audio.set_mono(guild_id, bool(val))
        elif prop_name == "volume":
            audio.set_volume(guild_id, val)
    print(f"[SET AUDIO PROP] {prop_name}={val}")
    return val


def _effect_defer_interaction(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    interaction = runtime.event_context.get("interaction")
    if interaction is not None and hasattr(interaction, 'response') and not interaction.response.is_done():
        _schedule(interaction.response.defer())
    return None


def _effect_show_modal(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    modal = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    user = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    interaction = runtime.event_context.get("interaction")
    if modal is not None and interaction is not None and hasattr(interaction, 'response') and not interaction.response.is_done():
        import discord
        if isinstance(modal, dict):
            m = discord.ui.Modal(title=modal.get("title", "Modal"), custom_id=modal.get("id", ""))
            for row in modal.get("rows", []):
                if isinstance(row, dict) and row.get("type") == "text_input":
                    style = discord.TextStyle.short if row.get("style") == "short" else discord.TextStyle.long
                    ti = discord.ui.TextInput(
                        label=row.get("label", ""),
                        custom_id=row.get("id", ""),
                        style=style,
                        placeholder=row.get("placeholder", ""),
                        required=row.get("required", True),
                        min_length=row.get("min_length"),
                        max_length=row.get("max_length"),
                    )
                    m.add_item(ti)
                elif isinstance(row, dict) and row.get("type") == "component_row":
                    for comp in row.get("components", []):
                        if isinstance(comp, dict) and comp.get("type") == "text_input":
                            ti = discord.ui.TextInput(
                                label=comp.get("label", ""),
                                custom_id=comp.get("id", ""),
                                style=discord.TextStyle.long if comp.get("style") == "long" else discord.TextStyle.short,
                                placeholder=comp.get("placeholder", ""),
                                required=comp.get("required", True),
                                min_length=comp.get("min_length"),
                                max_length=comp.get("max_length"),
                            )
                            m.add_item(ti)
            _schedule(interaction.response.send_modal(m))
        elif hasattr(modal, 'title'):
            _schedule(interaction.response.send_modal(modal))
    print(f"[SHOW MODAL] {modal}")
    return None


def _effect_trigger_custom_event(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if args else ""
    data = kwargs.get("data")
    if runtime.bot_manager and hasattr(runtime.bot_manager, 'event_bus'):
        bus = runtime.bot_manager.event_bus
        if data:
            bus.fire_custom(name, data)
        else:
            bus.fire_custom(name)
    print(f"[TRIGGER CUSTOM EVENT] {name}")
    return None


def _effect_set_presence(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    activity_type = str(args[0]) if len(args) > 0 else "playing"
    text = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    bot_inst = runtime.event_context.get("bot")
    if bot_inst is not None and hasattr(bot_inst, 'change_presence'):
        import discord
        activity_map = {
            "playing": discord.Game,
            "listening": discord.Activity,
            "watching": discord.Activity,
            "competing": discord.Activity,
        }
        act_type = activity_map.get(activity_type.lower(), discord.Game)
        if activity_type.lower() == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=text)
        elif activity_type.lower() == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
        elif activity_type.lower() == "competing":
            activity = discord.Activity(type=discord.ActivityType.competing, name=text)
        else:
            activity = discord.Game(name=text)
        _schedule(bot_inst.change_presence(activity=activity))
    print(f"[SET PRESENCE] {activity_type} {text}")
    return None


def _effect_set_status(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    status = str(_resolve_obj(runtime, args[0], scope) or "online") if len(args) > 0 else "online"
    bot_inst = runtime.event_context.get("bot")
    if bot_inst is not None and hasattr(bot_inst, 'change_presence'):
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
            "offline": discord.Status.offline,
        }
        _schedule(bot_inst.change_presence(status=status_map.get(status.lower(), discord.Status.online)))
    print(f"[SET STATUS] {status}")
    return None


def _effect_shutdown_bot(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    bot_inst = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("bot")
    if bot_inst is not None and hasattr(bot_inst, 'close'):
        _schedule(bot_inst.close())
    print(f"[SHUTDOWN]")
    return None


def _effect_load_members(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if args else None
    if guild is not None and hasattr(guild, 'chunk'):
        _schedule(guild.chunk())
    print(f"[LOAD MEMBERS] {guild}")
    return None


def _effect_send_typing(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    channel = _resolve_obj(runtime, args[0], scope) if args else None
    if channel is not None and hasattr(channel, 'typing'):
        _schedule(channel.typing())
    print(f"[SEND TYPING] {channel}")
    return None


def _effect_register_embed_template(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if args else ""
    runtime.embed_templates[name] = body
    print(f"[REGISTER EMBED TEMPLATE] {name}")
    return None


def _effect_register_webhook(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    name = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    url = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    store_in = kwargs.get("store_in")
    result = {"type": "webhook", "name": name, "url": url}
    _store_result(runtime, store_in, result, scope)
    print(f"[REGISTER WEBHOOK] {name}")
    return result


def _effect_webhook_send(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    webhook = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    content = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if webhook is not None and content is not None:
        if hasattr(webhook, 'send'):
            _schedule(webhook.send(str(content)))
        elif isinstance(webhook, dict):
            import discord
            url = webhook.get("url", "")
            if url:
                wh = discord.Webhook.from_url(url, client=runtime.current_bot)
                _schedule(wh.send(str(content)))
    print(f"[WEBHOOK SEND] {webhook}")
    return None


def _effect_webhook_delete(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    webhook = _resolve_obj(runtime, args[0], scope) if args else None
    if webhook is not None and hasattr(webhook, 'delete'):
        _schedule(webhook.delete())
    elif isinstance(webhook, dict):
        import discord
        url = webhook.get("url", "")
        if url:
            wh = discord.Webhook.from_url(url, client=runtime.current_bot)
            _schedule(wh.delete())
    print(f"[WEBHOOK DELETE] {webhook}")
    return None


def _effect_set_cooldown(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    target = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    duration = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if target is not None and duration is not None:
        cd_seconds = float(duration) if not isinstance(duration, (int, float)) else duration
        import time
        runtime.event_context.set("cooldown", time.time() + cd_seconds)
        print(f"[SET COOLDOWN] {target} = {cd_seconds}s")
    return None


def _effect_set_cooldown_message(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    target = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    msg = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if target is not None:
        runtime.event_context.set("cooldown_message", msg)
        print(f"[SET COOLDOWN MESSAGE] {target} = {msg}")
    return None


def _effect_set_cooldown_bypass(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    target = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    bypass = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if target is not None:
        runtime.event_context.set("cooldown_bypass", bypass)
        print(f"[SET COOLDOWN BYPASS] {target} = {bypass}")
    return None


def _effect_set_prefix(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    target = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    prefix = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if target is not None:
        runtime.option_vars["prefix"] = prefix
        print(f"[SET PREFIX] {target} = {prefix}")
    return None


def _effect_webhook_edit(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    webhook = _resolve_obj(runtime, args[0], scope) if args else None
    name = str(_resolve_obj(runtime, kwargs.get("name"), scope) or "") if kwargs.get("name") else None
    avatar_url = str(_resolve_obj(runtime, kwargs.get("avatar"), scope) or "") if kwargs.get("avatar") else None
    if webhook is not None:
        if hasattr(webhook, 'edit'):
            edit_kwargs = {}
            if name:
                edit_kwargs["name"] = name
            if avatar_url:
                import discord
                import aiohttp
                async def fetch_and_edit():
                    async with aiohttp.ClientSession() as session:
                        async with session.get(avatar_url) as resp:
                            edit_kwargs["avatar"] = await resp.read()
                    await webhook.edit(**edit_kwargs)
                _schedule(fetch_and_edit())
            else:
                _schedule(webhook.edit(**edit_kwargs))
        elif isinstance(webhook, dict):
            import discord
            url = webhook.get("url", "")
            if url:
                wh = discord.Webhook.from_url(url, client=runtime.current_bot)
                _schedule(wh.edit(name=name or wh.name))
    print(f"[WEBHOOK EDIT] {webhook}")
    return None


def _effect_update_command(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    cmd_name = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else None
    new_prefixes = kwargs.get("prefixes")
    new_permissions = kwargs.get("permissions")
    new_cooldown = kwargs.get("cooldown")
    enabled = kwargs.get("enabled", True)

    if cmd_name:
        for c in runtime.registered_commands:
            if c.name == cmd_name or cmd_name in (c.aliases or []):
                if new_prefixes is not None:
                    c.prefixes = new_prefixes
                if new_cooldown is not None:
                    c.cooldown = new_cooldown
                print(f"[UPDATE COMMAND] {cmd_name} updated")
                return {"updated": True, "name": cmd_name}

    print(f"[UPDATE COMMAND] {cmd_name} not found")
    return None


def _effect_execute(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    command_text = str(_resolve_obj(runtime, args[0], scope) or "") if args else ""
    executor = _resolve_obj(runtime, kwargs.get("as"), scope) if kwargs.get("as") else None
    store_in = kwargs.get("store_in")
    result = None

    if command_text:
        message = runtime.event_context.get("message")
        channel = runtime.event_context.get("channel")
        if message and hasattr(message, 'channel') and hasattr(message, 'author'):
            ev_ctx = runtime.event_context
            saved_content = ev_ctx.get("message_content", "")
            ev_ctx.set("message_content", command_text)

            bot_mgr = getattr(runtime, 'bot_manager', None)
            if bot_mgr and hasattr(bot_mgr, 'command_registry'):
                import asyncio
                fake_msg = type('FakeMessage', (), {
                    'content': command_text,
                    'author': executor or message.author,
                    'channel': message.channel,
                    'guild': message.guild,
                    'created_at': None,
                    'id': 0,
                })()
                _schedule(bot_mgr.command_registry.handle_prefix(
                    fake_msg,
                    ev_ctx.get("bot_name", "default"),
                    runtime,
                    bot_mgr.event_bus,
                ))
            ev_ctx.set("message_content", saved_content)
            result = {"executed": True, "command": command_text}

    _store_result(runtime, store_in, result, scope)
    print(f"[EXECUTE] {command_text}")
    return result


def _effect_edit_channel(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    ch = _resolve_obj(runtime, args[0], scope) if args else None
    if ch is not None and hasattr(ch, 'edit'):
        edit_kwargs = {}
        for key, val in kwargs.items():
            resolved = _resolve_obj(runtime, val, scope) if hasattr(val, 'line') else val
            edit_kwargs[key] = resolved
        if edit_kwargs:
            _schedule(ch.edit(**edit_kwargs))
    print(f"[EDIT CHANNEL] {args}")
    return None


def _effect_retrieve(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    store_in = kwargs.get("store_in")
    _store_result(runtime, store_in, None, scope)
    print(f"[RETRIEVE] {args} -> {store_in}")
    return None


def _effect_retrieve_dispatch(effect_type: str, runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    store_in = kwargs.get("store_in")
    result = None

    if not args:
        _store_result(runtime, store_in, None, scope)
        return None

    if effect_type == "retrieve_member":
        guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
        if guild and hasattr(guild, 'get_member'):
            identifier = args[1] if len(args) > 1 else None
            if identifier:
                try:
                    result = guild.get_member(int(identifier))
                except (ValueError, TypeError):
                    result = guild.get_member_named(str(identifier))
        if result is None:
            result = runtime.event_context.get("member")

    elif effect_type == "retrieve_message":
        channel = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("channel")
        msg_id = args[1] if len(args) > 1 else None
        if channel and msg_id and hasattr(channel, 'fetch_message'):
            try:
                msg_id_int = int(msg_id) if not isinstance(msg_id, int) else msg_id
                _schedule(_async_retrieve(channel.fetch_message(msg_id_int), runtime, store_in, scope))
                return None
            except (ValueError, TypeError):
                pass

    elif effect_type == "retrieve_messages":
        channel = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("channel")
        limit = int(args[1]) if len(args) > 1 and args[1] else 50
        if channel and hasattr(channel, 'history'):
            _schedule(_async_retrieve_list(channel.history(limit=limit).flatten(), runtime, store_in, scope))
            return None

    elif effect_type == "retrieve_user":
        user_id = args[0] if args else None
        bot_inst = runtime.current_bot
        if user_id and bot_inst and hasattr(bot_inst, 'fetch_user'):
            try:
                uid = int(user_id) if not isinstance(user_id, int) else user_id
                _schedule(_async_retrieve(bot_inst.fetch_user(uid), runtime, store_in, scope))
                return None
            except (ValueError, TypeError):
                pass

    elif effect_type == "retrieve_channel":
        guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
        channel_id = args[1] if len(args) > 1 else None
        if channel_id and guild and hasattr(guild, 'get_channel'):
            try:
                result = guild.get_channel(int(channel_id))
            except (ValueError, TypeError):
                result = None

    elif effect_type == "retrieve_bans":
        guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
        if guild and hasattr(guild, 'bans'):
            _schedule(_async_retrieve_list(guild.bans().flatten(), runtime, store_in, scope))
            return None

    elif effect_type == "retrieve_invites":
        guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
        if guild and hasattr(guild, 'invites'):
            _schedule(_async_retrieve_list(guild.invites(), runtime, store_in, scope))
            return None

    elif effect_type == "retrieve_webhooks":
        guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
        if guild and hasattr(guild, 'webhooks'):
            _schedule(_async_retrieve_list(guild.webhooks(), runtime, store_in, scope))
            return None

    elif effect_type == "retrieve_owner":
        guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
        if guild and hasattr(guild, 'owner'):
            result = guild.owner

    elif effect_type == "retrieve_audit_logs":
        guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
        limit = int(args[1]) if len(args) > 1 and args[1] else 50
        if guild and hasattr(guild, 'audit_logs'):
            _schedule(_async_retrieve_list(guild.audit_logs(limit=limit).flatten(), runtime, store_in, scope))
            return None

    elif effect_type == "retrieve_thread_members":
        thread = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("channel")
        if thread and hasattr(thread, 'fetch_members'):
            _schedule(_async_retrieve_list(thread.fetch_members(), runtime, store_in, scope))
            return None

    _store_result(runtime, store_in, result, scope)
    return result


async def _async_retrieve(coro, runtime, store_in, scope):
    try:
        result = await coro
        _store_result(runtime, store_in, result, scope)
        return result
    except Exception as e:
        print(f"[RETRIEVE ERROR] {e}")
        _store_result(runtime, store_in, None, scope)
        return None


async def _async_retrieve_list(coro, runtime, store_in, scope):
    try:
        result = await coro
        _store_result(runtime, store_in, result, scope)
        return result
    except Exception as e:
        print(f"[RETRIEVE LIST ERROR] {e}")
        _store_result(runtime, store_in, [], scope)
        return []


def _effect_set_channel_topic(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    channel = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    topic = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if channel is not None and hasattr(channel, 'edit'):
        _schedule(channel.edit(topic=topic))
    return None


def _effect_set_channel_slowmode(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    channel = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    slowmode = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else 0
    try:
        slowmode = int(parse_timespan(str(slowmode))) if isinstance(slowmode, str) else int(slowmode)
    except (TypeError, ValueError):
        slowmode = 0
    if channel is not None and hasattr(channel, 'edit'):
        _schedule(channel.edit(slowmode_delay=slowmode))
    return None


def _effect_set_channel_nsfw(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    channel = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    nsfw = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else False
    if isinstance(nsfw, str):
        nsfw = nsfw.lower() in ("true", "yes", "1")
    if channel is not None and hasattr(channel, 'edit'):
        _schedule(channel.edit(nsfw=bool(nsfw)))
    return None


def _effect_set_channel_name(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    ch = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    name = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if ch is not None and hasattr(ch, 'edit'):
        _schedule(ch.edit(name=name))
    return None


def _effect_set_channel_position(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    ch = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    pos = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else 0
    try:
        pos = int(pos)
    except (TypeError, ValueError):
        pos = 0
    if ch is not None and hasattr(ch, 'edit'):
        _schedule(ch.edit(position=pos))
    return None


def _effect_set_channel_parent(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    ch = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    parent = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if ch is not None and parent is not None and hasattr(ch, 'edit'):
        _schedule(ch.edit(category=parent))
    return None


def _effect_clone_channel(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    ch = _resolve_obj(runtime, args[0], scope) if args else None
    store_in = kwargs.get("store_in")
    result = None
    if ch is not None and hasattr(ch, 'clone'):
        coro = ch.clone()
        _schedule(coro)
    _store_result(runtime, store_in, result, scope)
    return None


def _effect_add_reaction(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    emoji = str(_resolve_obj(runtime, args[1], scope) or "👍") if len(args) > 1 else "👍"
    if msg is not None and hasattr(msg, 'add_reaction'):
        _schedule(msg.add_reaction(emoji))
    return None


def _effect_remove_reaction(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    emoji = str(_resolve_obj(runtime, args[1], scope) or "👍") if len(args) > 1 else "👍"
    member = _resolve_obj(runtime, args[2], scope) if len(args) > 2 else None
    if msg is not None and hasattr(msg, 'remove_reaction'):
        _schedule(msg.remove_reaction(emoji, member))
    return None


def _effect_clear_reactions(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    msg = _resolve_obj(runtime, args[0], scope) if args else None
    if msg is not None and hasattr(msg, 'clear_reactions'):
        _schedule(msg.clear_reactions())
    return None


def _effect_set_role_name(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    name = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if role is not None and hasattr(role, 'edit'):
        _schedule(role.edit(name=name))
    return None


def _effect_set_role_color(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    color = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if role is not None and hasattr(role, 'edit'):
        _schedule(role.edit(color=parse_color(color)))
    return None


def _effect_set_role_permissions(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    perms = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else 0
    if role is not None and hasattr(role, 'edit'):
        import discord
        if isinstance(perms, str):
            perm_value = sum(v for k, v in PERMISSION_NAMES.items() if k in perms)
        elif isinstance(perms, (int, float)):
            perm_value = int(perms)
        else:
            perm_value = 0
        _schedule(role.edit(permissions=discord.Permissions(perm_value)))
    return None


def _effect_set_role_hoist(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    hoist = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else False
    if isinstance(hoist, str):
        hoist = hoist.lower() in ("true", "yes", "1")
    if role is not None and hasattr(role, 'edit'):
        _schedule(role.edit(hoist=bool(hoist)))
    return None


def _effect_set_role_mentionable(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    mentionable = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else False
    if isinstance(mentionable, str):
        mentionable = mentionable.lower() in ("true", "yes", "1")
    if role is not None and hasattr(role, 'edit'):
        _schedule(role.edit(mentionable=bool(mentionable)))
    return None


def _effect_delete_role(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    role = _resolve_obj(runtime, args[0], scope) if args else None
    if role is not None and hasattr(role, 'delete'):
        _schedule(role.delete())
    return None


def _effect_set_guild_name(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    name = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(name=name))
    return None


def _effect_set_guild_icon(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    icon_path = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if guild is not None and hasattr(guild, 'edit'):
        try:
            with open(icon_path, "rb") as f:
                icon_data = f.read()
            _schedule(guild.edit(icon=icon_data))
        except Exception:
            pass
    return None


def _effect_set_guild_banner(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    banner_path = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if guild is not None and hasattr(guild, 'edit'):
        try:
            with open(banner_path, "rb") as f:
                banner_data = f.read()
            _schedule(guild.edit(banner=banner_data))
        except Exception:
            pass
    return None


def _effect_set_guild_description(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    desc = str(_resolve_obj(runtime, args[1], scope) or "") if len(args) > 1 else ""
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(description=desc))
    return None


def _effect_set_verification_level(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    level = str(_resolve_obj(runtime, args[1], scope) or "none") if len(args) > 1 else "none"
    level_map = {
        "none": discord.VerificationLevel.none,
        "low": discord.VerificationLevel.low,
        "medium": discord.VerificationLevel.medium,
        "high": discord.VerificationLevel.high,
        "very_high": discord.VerificationLevel.highest,
    }
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(verification_level=level_map.get(level.lower(), discord.VerificationLevel.none)))
    return None


def _effect_set_guild_notification_level(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    level = str(_resolve_obj(runtime, args[1], scope) or "all") if len(args) > 1 else "all"
    level_map = {
        "all": discord.NotificationLevel.all_messages,
        "mentions": discord.NotificationLevel.only_mentions,
        "nothing": discord.NotificationLevel.only_mentions,
    }
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(default_notifications=level_map.get(level.lower(), discord.NotificationLevel.all_messages)))
    return None


def _effect_set_guild_nsfw_level(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    level = str(_resolve_obj(runtime, args[1], scope) or "default") if len(args) > 1 else "default"
    level_map = {
        "default": discord.NSFWLevel.default,
        "explicit": discord.NSFWLevel.explicit,
        "safe": discord.NSFWLevel.safe,
        "age_restricted": discord.NSFWLevel.age_restricted,
    }
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(nsfw_level=level_map.get(level.lower(), discord.NSFWLevel.default)))
    return None


def _effect_set_afk_channel(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(afk_channel=channel))
    return None


def _effect_set_afk_timeout(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    timeout = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else 300
    try:
        timeout = int(parse_timespan(str(timeout))) if isinstance(timeout, str) else int(timeout)
    except (TypeError, ValueError):
        timeout = 300
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(afk_timeout=timeout))
    return None


def _effect_set_system_channel(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(system_channel=channel))
    return None


def _effect_set_rules_channel(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(rules_channel=channel))
    return None


def _effect_set_public_updates_channel(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if len(args) > 0 else None
    channel = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    if guild is not None and hasattr(guild, 'edit'):
        _schedule(guild.edit(public_updates_channel=channel))
    return None


def _effect_modify_welcome_screen(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    guild = _resolve_obj(runtime, args[0], scope) if args else runtime.event_context.get("guild")
    if guild is not None:
        description = ""
        welcome_channels = []
        for stmt in body or []:
            if hasattr(stmt, 'effect_type'):
                if stmt.effect_type == "welcome_set_description":
                    description = str(_resolve_obj(runtime, stmt.arguments[0], scope) or "")
                elif stmt.effect_type == "welcome_add_channel":
                    ch = _resolve_obj(runtime, stmt.arguments[0], scope) if stmt.arguments else None
                    desc = str(_resolve_obj(runtime, stmt.arguments[1], scope) or "") if len(stmt.arguments) > 1 else ""
                    if ch and hasattr(ch, 'id'):
                        welcome_channels.append({"channel_id": ch.id, "description": desc})
        try:
            import discord
            ws = discord.WelcomeScreen(description=description or None, welcome_channels=welcome_channels) if hasattr(discord, 'WelcomeScreen') else {"description": description, "welcome_channels": welcome_channels}
            _schedule(guild.edit(welcome_screen=ws))
        except Exception as e:
            print(f"[MODIFY WELCOME SCREEN ERROR] {e}")
    print(f"[MODIFY WELCOME SCREEN]")
    return None


def _effect_add_reaction_role(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    emoji = str(_resolve_obj(runtime, args[0], scope) or "") if len(args) > 0 else ""
    role = _resolve_obj(runtime, args[1], scope) if len(args) > 1 else None
    channel = _resolve_obj(runtime, kwargs.get("channel"), scope) if kwargs.get("channel") else runtime.event_context.get("channel")
    message_id = _resolve_obj(runtime, kwargs.get("message"), scope) if kwargs.get("message") else None
    store_in = kwargs.get("store_in")
    result = {"type": "reaction_role", "emoji": emoji}

    if channel and message_id and role and hasattr(channel, 'fetch_message'):
        import asyncio
        async def setup_reaction_role():
            try:
                msg = await channel.fetch_message(int(message_id))
                await msg.add_reaction(emoji)
                guild_id = getattr(channel, 'guild', None) and channel.guild.id
                if guild_id:
                    key = f"reaction_role:{guild_id}:{message_id}:{emoji}"
                    runtime.global_scope.set(key, role.id)
                result["setup"] = True
            except Exception as e:
                print(f"[REACTION ROLE ERROR] {e}")
                result["error"] = str(e)
        _schedule(setup_reaction_role())

    _store_result(runtime, store_in, result, scope)
    print(f"[ADD REACTION ROLE] {emoji}")
    return result


def _effect_delete_invite(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    invite = _resolve_obj(runtime, args[0], scope) if args else None
    if invite is not None and hasattr(invite, 'delete'):
        _schedule(invite.delete())
    return None


def _effect_delete_scheduled_event(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    event = _resolve_obj(runtime, args[0], scope) if args else None
    if event is not None and hasattr(event, 'delete'):
        _schedule(event.delete())
    return None


def _effect_delete_sticker(runtime: Runtime, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
    sticker = _resolve_obj(runtime, args[0], scope) if args else None
    if sticker is not None and hasattr(sticker, 'delete'):
        _schedule(sticker.delete())
    return None
