from __future__ import annotations
from language.runtime import Runtime, Scope
from language.types import parse_color, parse_timespan
from typing import Any, Optional
import datetime


def process_section(runtime: Runtime, section_type: str, body: list, scope: Scope, **kwargs) -> Any:
    handlers = {
        "embed": _process_embed_section,
        "component_row": _process_row_section,
        "message": _process_message_section,
        "modal": _process_modal_section,
        "audio_load": _process_audio_load_section,
        "member_filter": _process_member_filter_section,
        "welcome_screen": _process_welcome_screen_section,
        "container": _process_container_section,
    }
    handler = handlers.get(section_type)
    if handler:
        return handler(runtime, body, scope, **kwargs)
    return None


def _process_embed_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> Any:
    import discord
    embed = discord.Embed()
    template_name = kwargs.get("template")
    if template_name and template_name in runtime.embed_templates:
        tmpl_body = runtime.embed_templates[template_name]
        runtime.execute_effect_list(tmpl_body, scope)

    for stmt in body:
        if hasattr(stmt, 'effect_type'):
            etype = stmt.effect_type
            if etype.startswith("embed_set_"):
                prop = etype[10:]
                val = runtime.evaluate(stmt.arguments[0], scope) if stmt.arguments else None
                _apply_embed_property(embed, prop, val)
            elif etype == "embed_add_field":
                name = str(runtime.evaluate(stmt.arguments[0], scope) or "")
                value = str(runtime.evaluate(stmt.arguments[1], scope) or "")
                inline = bool(stmt.arguments[2]) if len(stmt.arguments) > 2 else False
                if isinstance(inline, str):
                    inline = inline.lower() in ("true", "yes", "1")
                embed.add_field(name=name, value=value, inline=inline)
        elif isinstance(stmt, dict):
            _apply_dict_to_embed(embed, stmt)

    store_in = kwargs.get("store_in")
    if store_in:
        name = store_in if isinstance(store_in, str) else str(store_in)
        if name.startswith("_"):
            runtime.local_vars[name] = embed
        else:
            scope.set(name, embed)
            runtime.global_scope.set(name, embed)
    runtime.local_vars["last_embed"] = embed
    return embed


def _apply_embed_property(embed: Any, prop: str, val: Any) -> None:
    if val is None:
        return
    if prop == "title":
        embed.title = str(val)
    elif prop == "description":
        embed.description = str(val)
    elif prop == "color":
        embed.color = parse_color(val)
    elif prop == "author":
        embed.set_author(name=str(val) if val else "")
    elif prop == "author_icon":
        if embed.author:
            embed.set_author(name=embed.author.name or "", icon_url=str(val) if val else "")
    elif prop == "author_url":
        if embed.author:
            embed.set_author(name=embed.author.name or "", url=str(val) if val else "")
    elif prop == "image":
        embed.set_image(url=str(val) if val else "")
    elif prop == "thumbnail":
        embed.set_thumbnail(url=str(val) if val else "")
    elif prop == "footer":
        embed.set_footer(text=str(val) if val else "")
    elif prop == "footer_icon":
        if embed.footer:
            embed.set_footer(text=embed.footer.text or "", icon_url=str(val) if val else "")
    elif prop == "title_url":
        pass
    elif prop == "timestamp":
        try:
            embed.timestamp = val if isinstance(val, datetime.datetime) else datetime.datetime.fromisoformat(str(val))
        except (ValueError, TypeError):
            embed.timestamp = datetime.datetime.now()


def _apply_dict_to_embed(embed: Any, d: dict) -> None:
    for key, val in d.items():
        if key == "title":
            embed.title = str(val) if val else None
        elif key == "description":
            embed.description = str(val) if val else None
        elif key == "color":
            embed.color = parse_color(val)
        elif key == "field":
            if isinstance(val, dict):
                name = str(val.get("name", ""))
                value = str(val.get("value", ""))
                inline = bool(val.get("inline", False))
                embed.add_field(name=name, value=value, inline=inline)
        elif key == "footer":
            if isinstance(val, dict):
                embed.set_footer(**{k: str(v) for k, v in val.items() if v})
            elif val:
                embed.set_footer(text=str(val))
        elif key == "author":
            if isinstance(val, dict):
                embed.set_author(**{k: str(v) for k, v in val.items() if v})
            elif val:
                embed.set_author(name=str(val))
        elif key == "thumbnail":
            if isinstance(val, dict):
                embed.set_thumbnail(**{k: str(v) for k, v in val.items() if v})
            elif val:
                embed.set_thumbnail(url=str(val))
        elif key == "image":
            if isinstance(val, dict):
                embed.set_image(**{k: str(v) for k, v in val.items() if v})
            elif val:
                embed.set_image(url=str(val))
        elif key == "timestamp":
            try:
                embed.timestamp = val if isinstance(val, datetime.datetime) else datetime.datetime.fromisoformat(str(val))
            except (ValueError, TypeError):
                pass


def _process_row_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> dict:
    components = []
    for stmt in body:
        if hasattr(stmt, 'effect_type') and stmt.effect_type == "row_add_component":
            comp = runtime.evaluate(stmt.arguments[0], scope)
            if comp:
                components.append(comp)
        elif isinstance(stmt, (list, tuple)):
            for item in stmt:
                if item:
                    components.append(item)
    result = {"type": "component_row", "components": components}
    store_in = kwargs.get("store_in")
    if store_in:
        name = store_in if isinstance(store_in, str) else str(store_in)
        if name.startswith("_"):
            runtime.local_vars[name] = result
        else:
            scope.set(name, result)
            runtime.global_scope.set(name, result)
    runtime.local_vars["last_row"] = result
    return result


def _process_message_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> dict:
    content = None
    embeds = []
    components = []
    silent = kwargs.get("silent", False)
    for stmt in body:
        if hasattr(stmt, 'effect_type'):
            if stmt.effect_type == "message_set_content":
                content = runtime.evaluate(stmt.arguments[0], scope)
            elif stmt.effect_type == "message_add_embed":
                emb = runtime.evaluate(stmt.arguments[0], scope)
                if emb:
                    embeds.append(emb)
            elif stmt.effect_type == "message_add_row":
                row = runtime.evaluate(stmt.arguments[0], scope)
                if row:
                    components.append(row)
        elif isinstance(stmt, dict):
            if "embed" in stmt:
                import discord
                em = discord.Embed()
                _apply_dict_to_embed(em, stmt.get("embed", {}))
                embeds.append(em)
            if "content" in stmt:
                content = stmt["content"]
    result = {
        "type": "message",
        "data": {
            "content": str(content) if content else "",
            "embeds": embeds,
            "components": components,
            "silent": silent,
        },
    }
    store_in = kwargs.get("store_in")
    if store_in:
        name = store_in if isinstance(store_in, str) else str(store_in)
        if name.startswith("_"):
            runtime.local_vars[name] = result
        else:
            scope.set(name, result)
            runtime.global_scope.set(name, result)
    return result


def _process_modal_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> dict:
    import discord
    title = kwargs.get("title", "Modal")
    modal_id = kwargs.get("id", "")
    rows = []
    for stmt in body:
        if hasattr(stmt, 'effect_type'):
            if stmt.effect_type == "modal_add_row":
                row_data = runtime.evaluate(stmt.arguments[0], scope)
                if row_data:
                    rows.append(row_data)
        elif isinstance(stmt, dict):
            rows.append(stmt)
    result = {"type": "modal", "title": title, "id": modal_id, "rows": rows}
    store_in = kwargs.get("store_in")
    if store_in:
        name = store_in if isinstance(store_in, str) else str(store_in)
        if name.startswith("_"):
            runtime.local_vars[name] = result
        else:
            scope.set(name, result)
            runtime.global_scope.set(name, result)
    return result


def _process_audio_load_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> dict:
    from bot.audio_manager import AudioTrack, AudioPlaylist
    query = str(kwargs.get("query", ""))
    result = {}
    for stmt in body:
        if hasattr(stmt, 'effect_type'):
            if stmt.effect_type == "audio_track_load":
                first_track = query
                sc = Scope(scope)
                sc.set("loaded track", AudioTrack(title=query[:80]))
                runtime.execute_effect_list(stmt.body or [], sc)
                result = {"type": "track"}
            elif stmt.effect_type == "audio_playlist_load":
                sc = Scope(scope)
                pl = AudioPlaylist(name=query[:80])
                sc.set("loaded playlist", pl)
                runtime.execute_effect_list(stmt.body or [], sc)
                result = {"type": "playlist"}
            elif stmt.effect_type == "audio_no_matches":
                runtime.execute_effect_list(stmt.body or [], scope)
                result = {"type": "no_matches"}
            elif stmt.effect_type == "audio_load_error":
                sc = Scope(scope)
                sc.set("error", "Failed to load audio")
                runtime.execute_effect_list(stmt.body or [], sc)
                result = {"type": "error"}
    store_in = kwargs.get("store_in")
    if store_in:
        name = store_in if isinstance(store_in, str) else str(store_in)
        if name.startswith("_"):
            runtime.local_vars[name] = result
        else:
            scope.set(name, result)
            runtime.global_scope.set(name, result)
    return result


def _process_member_filter_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> list:
    guild = kwargs.get("guild", runtime.event_context.get("guild"))
    filter_var = kwargs.get("filter_var", "_m")
    members = []
    if guild and hasattr(guild, 'members'):
        for member in guild.members:
            scope.set(filter_var, member)
            all_match = True
            for stmt in body:
                result = runtime.evaluate(stmt, scope)
                if isinstance(result, dict):
                    val = result.get("value", True)
                    if not val:
                        all_match = False
                        break
            if all_match:
                members.append(member)
    store_in = kwargs.get("store_in")
    if store_in:
        name = store_in if isinstance(store_in, str) else str(store_in)
        if name.startswith("_"):
            runtime.local_vars[name] = members
        else:
            scope.set(name, members)
            runtime.global_scope.set(name, members)
    return members


def _process_welcome_screen_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> dict:
    description = ""
    welcome_channels = []
    for stmt in body:
        if hasattr(stmt, 'effect_type'):
            if stmt.effect_type == "welcome_set_description":
                description = str(runtime.evaluate(stmt.arguments[0], scope) or "")
            elif stmt.effect_type == "welcome_add_channel":
                ch = runtime.evaluate(stmt.arguments[0], scope) if stmt.arguments else None
                desc = str(runtime.evaluate(stmt.arguments[1], scope) or "") if len(stmt.arguments) > 1 else ""
                if ch and hasattr(ch, 'id'):
                    welcome_channels.append({"channel_id": ch.id, "description": desc})
    return {"description": description, "welcome_channels": welcome_channels}


def _process_container_section(runtime: Runtime, body: list, scope: Scope, **kwargs) -> dict:
    container_id = kwargs.get("id")
    content = []
    for stmt in body:
        if hasattr(stmt, 'effect_type'):
            if stmt.effect_type == "container_add_gallery":
                urls = runtime.evaluate(stmt.arguments[0], scope) if stmt.arguments else []
                content.append({"type": "media_gallery", "urls": urls})
            elif stmt.effect_type == "container_add_separator":
                content.append({"type": "separator"})
            elif stmt.effect_type == "container_add_section":
                section_data = runtime.evaluate(stmt.arguments[0], scope) if stmt.arguments else {}
                content.append(section_data)
            elif stmt.effect_type == "container_add_row":
                row_data = runtime.evaluate(stmt.arguments[0], scope) if stmt.arguments else {}
                content.append(row_data)
    result = {"type": "container", "id": container_id, "content": content}
    store_in = kwargs.get("store_in")
    if store_in:
        name = store_in if isinstance(store_in, str) else str(store_in)
        if name.startswith("_"):
            runtime.local_vars[name] = result
        else:
            scope.set(name, result)
            runtime.global_scope.set(name, result)
    return result


class SectionDefinitions:
    @staticmethod
    def get_section(name: str) -> dict[str, Any]:
        sections = {
            "embed": {
                "description": "Build a Discord embed",
                "children": ["set title", "set description", "set color", "set author",
                           "set image", "set thumbnail", "set footer", "set timestamp",
                           "add field"],
                "handler": _process_embed_section,
            },
            "component row": {
                "description": "Build a component action row",
                "children": ["add button", "add dropdown"],
                "handler": _process_row_section,
            },
            "message": {
                "description": "Build a rich message with embeds and components",
                "children": ["set content", "make embed", "add row"],
                "handler": _process_message_section,
            },
            "modal": {
                "description": "Build a modal dialog",
                "children": ["set title", "add text input", "add dropdown"],
                "handler": _process_modal_section,
            },
            "audio load": {
                "description": "Load audio from URL or search query",
                "children": ["on track load", "on playlist load", "on load error", "on no matches"],
                "handler": _process_audio_load_section,
            },
            "member filter": {
                "description": "Filter guild members by conditions",
                "children": ["filter conditions"],
                "handler": _process_member_filter_section,
            },
            "welcome screen": {
                "description": "Modify guild welcome screen",
                "children": ["set description", "add welcome channel"],
                "handler": _process_welcome_screen_section,
            },
            "container": {
                "description": "Build a components V2 container",
                "children": ["add media gallery", "add separator", "add section", "add row"],
                "handler": _process_container_section,
            },
        }
        return sections.get(name, {})
