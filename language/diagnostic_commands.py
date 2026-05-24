from __future__ import annotations
from language.runtime import Runtime, Scope, EventContext
from language.parser import Parser
from language.lexer import Lexer
from typing import Any


COMMANDS = {}


def register_diagnostic_commands(runtime: Runtime) -> None:
    global COMMANDS
    registry = getattr(runtime, 'command_registry', None)
    if registry is None:
        bot_mgr = getattr(runtime, 'bot_manager', None)
        if bot_mgr:
            registry = bot_mgr.command_registry
    if registry is None:
        return

    COMMANDS = {
        "test": _cmd_test,
        "reload": _cmd_reload,
        "scripts": _cmd_scripts,
        "eval": _cmd_eval,
        "inspect": _cmd_inspect,
        "debug": _cmd_debug,
        "simulate": _cmd_simulate,
        "lint": _cmd_lint,
    }

    for cmd_name, handler in COMMANDS.items():
        registry.register_diagnostic(cmd_name, handler)


def _get_prefix(runtime: Runtime) -> str:
    return runtime.option_vars.get("prefix", "!")


async def _cmd_test(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    scenario = args[0] if args else "all"
    lines = [f"**Test: {scenario}**"]

    if scenario in ("all", "parser"):
        script_count = len(getattr(runtime, 'script_manager', None) and runtime.script_manager.scripts or [])
        lines.append(f"- Scripts loaded: {script_count}")

    if scenario in ("all", "events"):
        event_count = len(runtime.event_handlers)
        lines.append(f"- Event handlers: {event_count}")

    if scenario in ("all", "commands"):
        cmd_count = len(runtime.registered_commands)
        slash_count = len(runtime.slash_commands)
        lines.append(f"- Prefix commands: {cmd_count}")
        lines.append(f"- Slash commands: {slash_count}")

    if scenario in ("all", "variables"):
        var_count = len(runtime.global_scope.variables)
        lines.append(f"- Global variables: {var_count}")

    if scenario in ("all", "bot"):
        bot_count = len(runtime.bot_instances)
        lines.append(f"- Bot instances: {bot_count}")
        for name, bot in runtime.bot_instances.items():
            ready = "ready" if hasattr(bot, 'is_ready') and bot.is_ready() else "not ready"
            lines.append(f"  - {name}: {ready}")

    if len(lines) == 1:
        lines.append("No matching test scenarios found.")

    return "\n".join(lines)


async def _cmd_reload(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    script_mgr = getattr(runtime, 'script_manager', None)
    if not script_mgr:
        return "No script manager available."

    if args:
        name = args[0]
        sf = script_mgr.get_script(name)
        if not sf:
            return f"Script `{name}` not found."
        sf = script_mgr.reload_script(sf.path)
        status = "OK" if not sf.error else f"ERROR: {sf.error}"
        return f"Reloaded `{sf.name}`: {status}"
    else:
        loaded = script_mgr.reload_all()
        good = sum(1 for sf in loaded if not sf.error)
        bad = len(loaded) - good
        return f"Reloaded {len(loaded)} scripts ({good} OK, {bad} errors)."


async def _cmd_scripts(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    script_mgr = getattr(runtime, 'script_manager', None)
    if not script_mgr:
        return "No script manager available."
    summary = script_mgr.get_summary()
    if not summary:
        return "No scripts loaded."
    lines = [f"**Scripts ({len(summary)}):**"]
    for s in summary:
        status = "OK" if not s["error"] else "ERR"
        lines.append(f"- `{s['name']}` [{status}]")
        if s["events"]:
            lines.append(f"  events: {', '.join(s['events'][:5])}")
        if s["commands"]:
            lines.append(f"  commands: {', '.join(s['commands'][:5])}")
        if s["error"]:
            lines.append(f"  error: {s['error']}")
    return "\n".join(lines)


async def _cmd_eval(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    if not args:
        return "Usage: `!eval <expression>`"
    expr_text = " ".join(args)
    try:
        from language.parser import Parser
        from language.runtime import Scope
        parser = Parser(expr_text)
        expr = parser.parse_expression()
        scope = Scope(runtime.global_scope)
        result = runtime.evaluate(expr, scope)
        return f"**Result:** {repr(result)}"
    except Exception as e:
        return f"**Error:** {type(e).__name__}: {e}"


async def _cmd_inspect(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    target = args[0] if args else "help"
    lines = []

    if target == "help":
        lines.append("**Inspect targets:**")
        lines.append("- `commands` — registered commands")
        lines.append("- `events` — event handlers")
        lines.append("- `options` — script options")
        lines.append("- `variables` — global variables")
        lines.append("- `functions` — registered functions")
        lines.append("- `bots` — bot instances")
        lines.append("- `<variable_name>` — specific variable value")
        return "\n".join(lines)

    if target == "commands":
        lines.append(f"**Commands ({len(runtime.registered_commands)}):**")
        for cmd in runtime.registered_commands:
            name = getattr(cmd, 'name', '?')
            pfx = getattr(cmd, 'prefixes', []) or []
            perm = getattr(cmd, 'permissions', None)
            lines.append(f"- `{name}` prefixes={pfx} perms={perm}")
        for cmd in runtime.slash_commands:
            name = getattr(cmd, 'name', '?')
            lines.append(f"- `/ {name}` (slash)")

    elif target == "events":
        lines.append(f"**Events ({len(runtime.event_handlers)}):**")
        for ev in runtime.event_handlers:
            etype = getattr(ev, 'event_type', '?')
            vals = getattr(ev, 'event_values', []) or []
            lines.append(f"- `on {etype}:` vals={vals}")
        for evt_name, handlers in runtime.custom_event_handlers.items():
            lines.append(f"- `on custom {evt_name}:` ({len(handlers)} handlers)")

    elif target == "options":
        lines.append("**Options:**")
        for key, val in runtime.option_vars.items():
            lines.append(f"- `{key}` = {val}")

    elif target == "variables":
        lines.append(f"**Global Variables ({len(runtime.global_scope.variables)}):**")
        for key, val in list(runtime.global_scope.variables.items())[:50]:
            lines.append(f"- `{{{key}}}` = {repr(val)[:60]}")
        if len(runtime.global_scope.variables) > 50:
            lines.append(f"... and {len(runtime.global_scope.variables) - 50} more")

    elif target == "functions":
        lines.append(f"**Functions ({len(runtime.functions)}):**")
        for name, fn in runtime.functions.items():
            params = getattr(fn, 'parameters', [])
            rtype = getattr(fn, 'return_type', 'any')
            lines.append(f"- `{name}({', '.join(p.name for p in params)}) :: {rtype}`")

    elif target == "bots":
        lines.append(f"**Bots ({len(runtime.bot_instances)}):**")
        for name, bot in runtime.bot_instances.items():
            uid = getattr(bot, 'user', None) and getattr(bot.user, 'id', '?')
            guilds = len(bot.guilds) if hasattr(bot, 'guilds') else '?'
            lines.append(f"- `{name}` id={uid} guilds={guilds}")

    else:
        val = runtime.global_scope.get(target)
        if val is None:
            val = runtime.option_vars.get(target)
        if val is None:
            val = getattr(runtime.event_context, 'values', {}).get(target)
        if val is None:
            from language.runtime import _resolve_identifier
            val = runtime._resolve_identifier(target, Scope(runtime.global_scope))
        lines.append(f"**{target}:**")
        lines.append(f"= {repr(val)}")

    return "\n".join(lines) if lines else "No results."


async def _cmd_debug(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    lines = ["**Debug Info**"]
    lines.append(f"- Event handlers: {len(runtime.event_handlers)}")
    lines.append(f"- Custom event handlers: {sum(len(v) for v in runtime.custom_event_handlers.values())}")
    lines.append(f"- Registered commands: {len(runtime.registered_commands)}")
    lines.append(f"- Slash commands: {len(runtime.slash_commands)}")
    lines.append(f"- Functions: {len(runtime.functions)}")
    lines.append(f"- Global variables: {len(runtime.global_scope.variables)}")
    lines.append(f"- Bot instances: {len(runtime.bot_instances)}")
    lines.append(f"- Embed templates: {len(runtime.embed_templates)}")
    lines.append(f"- Current event context keys: {list(runtime.event_context.values.keys())}")

    bot_mgr = getattr(runtime, 'bot_manager', None)
    if bot_mgr:
        lines.append(f"- Audio queues: {len(bot_mgr.audio_manager.guild_states) if hasattr(bot_mgr.audio_manager, 'guild_states') else 0}")

    script_mgr = getattr(runtime, 'script_manager', None)
    if script_mgr:
        lines.append(f"- Scripts loaded: {len(script_mgr.scripts) if hasattr(script_mgr, 'scripts') else 0}")

    import sys
    lines.append(f"- Python: {sys.version}")
    lines.append(f"- Effect handlers: {len(runtime.effect_handlers)}")
    lines.append(f"- Expression handlers: {len(runtime.expression_handlers)}")
    lines.append(f"- Condition handlers: {len(runtime.condition_handlers)}")

    return "\n".join(lines)


async def _cmd_simulate(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    if not args:
        return "Usage: `!simulate <event_type> [key=value...]`\nExample: `!simulate message content=Hello author=1234`"

    event_type = args[0]
    event_data = {}
    for arg in args[1:]:
        if "=" in arg:
            key, val = arg.split("=", 1)
            event_data[key.strip()] = val.strip()

    sim_ctx = EventContext()
    sim_ctx.bot_name = ctx.get("bot_name", "default")
    for key, val in event_data.items():
        sim_ctx.set(key, val)

    if event_type == "message":
        sim_ctx.set("message", event_data.get("content", ""))
        channel = runtime.event_context.get("channel")
        if channel:
            sim_ctx.set("channel", channel)

    matched = 0
    for ev in runtime.event_handlers:
        evt = getattr(ev, 'event_type', None)
        if evt == event_type:
            import asyncio
            scope = Scope(runtime.global_scope)
            try:
                runtime.event_context = sim_ctx
                runtime.execute_effect_list(ev.body, scope)
                matched += 1
            except Exception as e:
                print(f"[SIMULATE ERROR] {e}")
            finally:
                runtime.event_context = ctx

    if matched == 0:
        custom_handlers = runtime.custom_event_handlers.get(event_type, [])
        for ev in custom_handlers:
            scope = Scope(runtime.global_scope)
            try:
                runtime.event_context = sim_ctx
                runtime.execute_effect_list(ev.body, scope)
                matched += 1
            except Exception:
                pass
            finally:
                runtime.event_context = ctx

    if matched == 0:
        return f"No handlers found for event `{event_type}`."
    return f"Simulated `{event_type}` — triggered {matched} handler(s)."


async def _cmd_lint(runtime: Runtime, ctx: EventContext, args: list[str]) -> str:
    script_mgr = getattr(runtime, 'script_manager', None)
    if not script_mgr:
        return "No script manager available."

    scripts_dir = getattr(script_mgr, 'scripts_dir', 'scripts')
    import os, glob as glob_module
    script_files = glob_module.glob(os.path.join(scripts_dir, "*.discord"))
    if not script_files:
        return f"No `.discord` scripts found in `{scripts_dir}/`."

    lines = [f"**Linting {len(script_files)} scripts in `{scripts_dir}/`:**"]
    total_errors = 0

    for filepath in sorted(script_files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            lines.append(f"- `{filename}`: **ERROR reading file**: {e}")
            total_errors += 1
            continue

        lexer = Lexer(source)
        try:
            tokens = lexer.tokenize()
        except Exception as e:
            lines.append(f"- `{filename}`: **LEXER ERROR**: {e}")
            total_errors += 1
            continue

        parser = Parser(source)
        try:
            script = parser.parse()
            event_count = len(script.events)
            cmd_count = len(script.commands)
            fn_count = len(script.functions)
            bot_count = len(script.bot_defs)
            lines.append(f"- `{filename}`: OK ({event_count} events, {cmd_count} commands, {fn_count} functions, {bot_count} bot defs)")
        except Exception as e:
            loc = getattr(e, 'node', None)
            if loc:
                lines.append(f"- `{filename}`: **PARSE ERROR** Line {loc.line}:{loc.column}: {e}")
            else:
                lines.append(f"- `{filename}`: **PARSE ERROR**: {e}")
            total_errors += 1

    if total_errors == 0:
        lines.append("\n**All scripts pass lint!**")
    else:
        lines.append(f"\n**{total_errors} error(s) found.**")

    return "\n".join(lines)
