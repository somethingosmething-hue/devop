from __future__ import annotations
from language.runtime import Runtime, Scope
from language.ast import CommandDecl, SlashCommandDecl
from typing import Any, Optional
import discord
import asyncio
import time
import inspect


class CommandRegistry:
    def __init__(self):
        self.cooldowns: dict[str, float] = {}
        self.diagnostic_commands: dict[str, Any] = {}
        self._registered_tree_commands: set[str] = set()

    def register_diagnostic(self, name: str, handler: Any) -> None:
        self.diagnostic_commands[name.lower()] = handler

    async def handle_diagnostic(self, message: discord.Message, bot_name: str, runtime: Runtime, event_bus: Any) -> bool:
        prefix = runtime.option_vars.get("prefix", "!")
        content = message.content
        if not content.startswith(prefix):
            return False
        rest = content[len(prefix):]
        args = rest.split()
        if not args:
            return False
        cmd_name = args[0].lower()
        if cmd_name not in self.diagnostic_commands:
            return False

        ctx = runtime.event_context
        ctx.set("bot", runtime.bot_instances.get(bot_name))
        ctx.set("message", message)
        ctx.set("author", message.author)
        ctx.set("channel", message.channel)
        ctx.set("guild", message.guild)
        ctx.set("command_name", cmd_name)
        ctx.set("prefix", prefix)
        ctx.set("bot_name", bot_name)

        handler = self.diagnostic_commands[cmd_name]
        try:
            result = await handler(runtime, ctx, args[1:])
            if result:
                from language.builtins.effects import _schedule
                _schedule(message.channel.send(result))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            try:
                await message.channel.send(f"**{cmd_name} error:** {e}\n```{tb[:500]}```")
            except Exception:
                pass
        return True

    async def register_slash_commands(self, client: discord.Client, bot_name: str,
                                       runtime: Any = None, event_bus: Any = None) -> None:
        tree = getattr(client, 'tree', None)
        if not tree:
            try:
                tree = discord.app_commands.CommandTree(client)
                client.tree = tree
            except AttributeError:
                return

        self._registered_tree_commands.clear()

        if runtime and hasattr(runtime, 'slash_commands'):
            for cmd in runtime.slash_commands:
                name_parts = cmd.name.split()
                parts = len(name_parts)
                desc = cmd.description or "No description"

                async def make_callback(cmd_name: str, eb=event_bus, bn=bot_name, rt=runtime):
                    async def callback(interaction: discord.Interaction):
                        if eb:
                            await eb.fire("slash command", bn, {
                                "interaction": interaction,
                                "string": cmd_name,
                                "user": interaction.user,
                                "member": getattr(interaction, 'user', None),
                                "channel": interaction.channel,
                                "guild": interaction.guild,
                                "bot": rt.bot_instances.get(bn) if hasattr(rt, 'bot_instances') else None,
                            })
                    return callback

                cb = make_callback(cmd.name)

                try:
                    if parts == 1:
                        tree.command(name=name_parts[0], description=desc)(cb)
                        self._registered_tree_commands.add(name_parts[0])
                    elif parts == 2:
                        parent_group = None
                        for g in tree.get_commands():
                            if isinstance(g, discord.app_commands.Group) and g.name == name_parts[0]:
                                parent_group = g
                                break
                        if not parent_group:
                            parent_group = discord.app_commands.Group(name=name_parts[0], description="")
                            tree.add_command(parent_group)
                            self._registered_tree_commands.add(name_parts[0])
                        parent_group.command(name=name_parts[1], description=desc)(cb)
                    elif parts == 3:
                        parent_group = None
                        for g in tree.get_commands():
                            if isinstance(g, discord.app_commands.Group) and g.name == name_parts[0]:
                                parent_group = g
                                break
                        if not parent_group:
                            parent_group = discord.app_commands.Group(name=name_parts[0], description="")
                            tree.add_command(parent_group)
                            self._registered_tree_commands.add(name_parts[0])
                        child_group = None
                        for g in parent_group.commands:
                            if isinstance(g, discord.app_commands.Group) and g.name == name_parts[1]:
                                child_group = g
                                break
                        if not child_group:
                            child_group = discord.app_commands.Group(name=name_parts[1], description="")
                            parent_group.add_command(child_group)
                        child_group.command(name=name_parts[2], description=desc)(cb)
                except Exception as e:
                    print(f"[CMD] Error registering '{cmd.name}': {e}")

        try:
            await tree.sync()
            print(f"[CMD] Slash commands synced for {bot_name}")
        except Exception as e:
            print(f"[CMD] Error syncing commands for {bot_name}: {e}")

    def is_tree_command(self, name: str) -> bool:
        return name in self._registered_tree_commands

    async def handle_prefix(self, message: discord.Message, bot_name: str, runtime: Runtime, event_bus: Any) -> bool:
        if await self.handle_diagnostic(message, bot_name, runtime, event_bus):
            return True

        commands = runtime.registered_commands
        content = message.content
        for cmd in commands:
            for prefix in cmd.prefixes:
                if not content.startswith(prefix):
                    continue
                rest = content[len(prefix):]
                args = rest.split()
                if not args:
                    continue
                cmd_name = args[0].lower()
                if cmd_name != cmd.name.lower() and cmd_name not in [a.lower() for a in cmd.aliases]:
                    continue

                ctx = runtime.event_context
                ctx.set("bot", runtime.bot_instances.get(bot_name))
                ctx.set("message", message)
                ctx.set("author", message.author)
                ctx.set("channel", message.channel)
                ctx.set("guild", message.guild)
                ctx.set("command_name", cmd.name)
                ctx.set("prefix", prefix)
                ctx.set("prefix_command", cmd)

                if cmd.permissions:
                    member = None
                    if hasattr(message, 'guild') and message.guild:
                        member = message.guild.get_member(message.author.id)
                    if member:
                        for perm_name in cmd.permissions:
                            perm_name = perm_name.replace(" ", "_")
                            if perm_name in ("administrator",) and hasattr(member, 'guild_permissions'):
                                if getattr(member.guild_permissions, perm_name, False):
                                    continue
                            if hasattr(member, 'guild_permissions'):
                                if not getattr(member.guild_permissions, perm_name, False) and perm_name != "administrator":
                                    err_msg = cmd.permission_message or "You don't have permission to use this command!"
                                    try:
                                        await message.reply(err_msg)
                                    except Exception:
                                        pass
                                    return True

                scope = Scope(runtime.global_scope)
                raw_args = args[1:]
                for i, (arg_name, arg_type, default_val) in enumerate(cmd.arguments):
                    val = raw_args[i] if i < len(raw_args) else (default_val if default_val is not None else None)
                    runtime.local_vars[f"arg-{i + 1}"] = val
                    runtime.local_vars[f"arg{i + 1}"] = val
                    runtime.local_vars[arg_name] = val

                if cmd.cooldown and message.author.id:
                    cd_key = f"{bot_name}:{cmd.name}:{message.author.id}"
                    now = time.time()
                    if cd_key in self.cooldowns:
                        remaining = self.cooldowns[cd_key] - now
                        if remaining > 0:
                            return True
                    from language.types import parse_timespan
                    cd_seconds = parse_timespan(str(cmd.cooldown))
                    self.cooldowns[cd_key] = now + cd_seconds

                try:
                    for stmt in cmd.trigger:
                        runtime.execute_effect_list([stmt], scope)
                except Exception as e:
                    print(f"[CMD] Error executing '{cmd.name}': {e}")
                    try:
                        await message.reply(f"Error: {e}")
                    except Exception:
                        pass
                return True
        return False

    def has_cooldown(self, key: str) -> bool:
        if key in self.cooldowns:
            if time.time() < self.cooldowns[key]:
                return True
            del self.cooldowns[key]
        return False
