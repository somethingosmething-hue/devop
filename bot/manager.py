from __future__ import annotations
from .event_bus import EventBus
from .command_registry import CommandRegistry
from .component_handler import ComponentHandler
from .audio_manager import AudioManager
from language.runtime import Runtime
from language.script_manager import ScriptManager
from language.ast import BotDefinition, EventHandler
from typing import Any, Optional
import discord
import asyncio
import os
import threading


class BotInstance:
    def __init__(self, name: str, token: str, intents: discord.Intents, runtime: Runtime,
                 event_bus: EventBus, command_registry: CommandRegistry,
                 component_handler: ComponentHandler, audio_manager: AudioManager):
        self.name = name
        self.token = token
        self.intents = intents
        self.runtime = runtime
        self.event_bus = event_bus
        self.command_registry = command_registry
        self.component_handler = component_handler
        self.audio_manager = audio_manager
        self.client: discord.Client | None = None
        self.ready = False
        self.loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def _create_client(self) -> discord.Client:
        intents = self.intents

        class DiscordBotClient(discord.Client):
            def __init__(self_bot, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self_bot.tree = discord.app_commands.CommandTree(self_bot) if hasattr(discord, 'app_commands') else None

            async def setup_hook(self_bot):
                if not hasattr(self_bot, 'tree') or self_bot.tree is None:
                    try:
                        self_bot.tree = discord.app_commands.CommandTree(self_bot)
                    except AttributeError:
                        pass
                @self_bot.tree.command(name="reload", description="Reload .dc scripts for this server")
                @discord.app_commands.describe(script="Script name to reload (omit or 'all' for all)")
                async def reload_slash(interaction: discord.Interaction, script: str = None):
                    try:
                        guild = interaction.guild
                        user = interaction.user
                        if guild and not guild.get_member(user.id).guild_permissions.administrator:
                            await interaction.response.send_message("You need **Administrator** permission to reload scripts.", ephemeral=True)
                            return
                        await interaction.response.defer()
                        sm = getattr(self.runtime, 'script_manager', None)
                        if not sm:
                            await interaction.edit_original_response(content="No script manager available.")
                            return
                        import time
                        guild_id = str(guild.id) if guild else ""

                        def fmt_line(msg: str) -> str:
                            import re
                            m = re.match(r"^Line (\d+:\d+):\s*(.*)", msg)
                            if m:
                                line_part, rest = m.groups()
                                first_line = rest.split("\n")[0].strip()
                                return f"• `{first_line}` (Line {line_part})"
                            return f"• {msg.split(chr(10))[0]}"

                        if script and script.lower() != "all":
                            paths = [p for p in sm.scan(guild_id) if script in p or script == os.path.splitext(os.path.basename(p))[0]]
                            if not paths:
                                await interaction.edit_original_response(content=f"Script `{script}` not found in this server.")
                                return
                            t0 = time.time()
                            sf = sm.reload_script(paths[0])
                            elapsed_ms = (time.time() - t0) * 1000
                            parts = []
                            if sf.error:
                                msg = str(sf.error)
                                parts.append("**__Errors:__**\n")
                                parts.append(f"⇄ *{sf.name}*\n{fmt_line(msg)}\n")
                                parts.append(f"\n⏲ Reloaded **{sf.name}** with errors. ({elapsed_ms:.0f}ms)")
                                parts.append(f"\n​     → 1 error")
                            else:
                                parts.append(f"⏲ Reloaded **{sf.name}** successfully. ({elapsed_ms:.0f}ms)")
                            await interaction.edit_original_response(content="\n".join(parts))
                            return

                        paths = sm.scan(guild_id) if guild_id else []
                        if not paths:
                            msg = "No scripts found for this server." if guild_id else "No guild context."
                            await interaction.edit_original_response(content=msg)
                            return
                        t0 = time.time()
                        per_file = {}
                        for path in paths:
                            sf = sm.reload_script(path)
                            if sf.error:
                                if sf.name not in per_file:
                                    per_file[sf.name] = []
                                per_file[sf.name].append(str(sf.error))
                        elapsed_ms = (time.time() - t0) * 1000
                        parts = []
                        if per_file:
                            parts.append("**__Errors:__**\n")
                            for fname in sorted(per_file):
                                parts.append(f"⇄ *{fname}*")
                                for err in per_file[fname]:
                                    parts.append(fmt_line(str(err)))
                                parts.append("")
                            total_err = sum(len(v) for v in per_file.values())
                            good = len(paths) - total_err
                            parts.append(f"⏲ Reloaded **{len(paths)}** scripts. ({elapsed_ms:.0f}ms)")
                            parts.append(f"​     → {total_err} error{'s' if total_err != 1 else ''}")
                        else:
                            parts.append(f"⏲ Reloaded **{len(paths)}** scripts successfully. ({elapsed_ms:.0f}ms)")
                        await interaction.edit_original_response(content="\n".join(parts))
                    except Exception as e:
                        import traceback
                        tb = traceback.format_exc()
                        print(f"[BOT] /reload error: {e}\n{tb}")
                        try:
                            await interaction.edit_original_response(content=f"**Error:** {e}")
                        except Exception:
                            pass
                await self.command_registry.register_slash_commands(self_bot, self.name, self.runtime, self.event_bus)

            async def on_ready(self_bot):
                self.ready = True
                self.client = self_bot
                self.loop = asyncio.get_event_loop()
                self.audio_manager.set_loop(self.loop)
                self.runtime.current_bot = self_bot
                self.runtime.bot_instances[self.name] = self_bot

                ev_ctx = self.runtime.event_context
                ev_ctx.set("bot", self_bot)

                await self.event_bus.fire("bot ready", self.name, {
                    "bot": self_bot,
                    "bot_name": self.name,
                })
                print(f"[BOT] {self.name} is ready!")

            async def on_message(self_bot, message):
                if message.author.bot:
                    return
                await self.event_bus.fire("message", self.name, {
                    "message": message,
                    "channel": message.channel,
                    "author": message.author,
                    "guild": message.guild,
                    "bot": self_bot,
                })
                await self.command_registry.handle_prefix(message, self.name, self.runtime, self.event_bus)

            async def on_message_edit(self_bot, before, after):
                if after.author.bot:
                    return
                await self.event_bus.fire("message edit", self.name, {
                    "message": after, "before": before, "author": after.author,
                    "channel": after.channel, "guild": after.guild, "bot": self_bot,
                    "string": before.content if before else "",
                })

            async def on_message_delete(self_bot, message):
                await self.event_bus.fire("message delete", self.name, {
                    "message": message, "channel": message.channel,
                    "guild": message.guild, "bot": self_bot,
                })

            async def on_bulk_message_delete(self_bot, messages):
                await self.event_bus.fire("bulk message delete", self.name, {
                    "messages": messages, "bot": self_bot,
                })

            async def on_reaction_add(self_bot, reaction, user):
                if user.bot:
                    return
                await self.event_bus.fire("reaction add", self.name, {
                    "message": reaction.message, "emote": reaction.emoji,
                    "user": user, "member": getattr(reaction.message.guild, 'get_member', lambda: None)(user.id),
                    "channel": reaction.message.channel, "guild": reaction.message.guild,
                    "bot": self_bot,
                })

            async def on_reaction_remove(self_bot, reaction, user):
                if user.bot:
                    return
                await self.event_bus.fire("reaction remove", self.name, {
                    "message": reaction.message, "emote": reaction.emoji,
                    "user": user, "channel": reaction.message.channel,
                    "guild": reaction.message.guild, "bot": self_bot,
                })

            async def on_reaction_clear(self_bot, message, reactions):
                await self.event_bus.fire("reaction clear", self.name, {
                    "message": message, "reactions": reactions,
                    "channel": message.channel, "guild": message.guild,
                    "bot": self_bot,
                })

            async def on_guild_join(self_bot, guild):
                await self.event_bus.fire("guild member join", self.name, {
                    "guild": guild, "bot": self_bot,
                })
                script_mgr = getattr(self.runtime, 'script_manager', None)
                if script_mgr:
                    script_mgr.ensure_guild_dir(str(guild.id))

            async def on_member_join(self_bot, member):
                await self.event_bus.fire("guild member join", self.name, {
                    "member": member, "user": member, "guild": member.guild,
                    "bot": self_bot,
                })

            async def on_member_remove(self_bot, member):
                await self.event_bus.fire("guild member leave", self.name, {
                    "member": member, "user": member, "guild": member.guild,
                    "bot": self_bot,
                })

            async def on_member_update(self_bot, before, after):
                await self.event_bus.fire("guild member update", self.name, {
                    "member": after, "user": after, "guild": after.guild,
                    "bot": self_bot,
                })

            async def on_guild_channel_create(self_bot, channel):
                await self.event_bus.fire("channel create", self.name, {
                    "channel": channel, "guild": channel.guild, "bot": self_bot,
                })

            async def on_guild_channel_delete(self_bot, channel):
                await self.event_bus.fire("channel delete", self.name, {
                    "channel": channel, "guild": channel.guild, "bot": self_bot,
                })

            async def on_guild_channel_update(self_bot, before, after):
                await self.event_bus.fire("channel edit", self.name, {
                    "channel": after, "guild": after.guild, "bot": self_bot,
                })

            async def on_thread_create(self_bot, thread):
                await self.event_bus.fire("thread create", self.name, {
                    "channel": thread, "guild": thread.guild, "bot": self_bot,
                })

            async def on_thread_delete(self_bot, thread):
                await self.event_bus.fire("thread delete", self.name, {
                    "channel": thread, "guild": thread.guild, "bot": self_bot,
                })

            async def on_thread_update(self_bot, before, after):
                await self.event_bus.fire("thread update", self.name, {
                    "channel": after, "guild": after.guild, "bot": self_bot,
                })

            async def on_voice_state_update(self_bot, member, before, after):
                if before.channel != after.channel:
                    if after.channel:
                        await self.event_bus.fire("voice join", self.name, {
                            "member": member, "user": member,
                            "channel": after.channel, "guild": after.channel.guild,
                            "bot": self_bot,
                        })
                    if before.channel:
                        await self.event_bus.fire("voice leave", self.name, {
                            "member": member, "user": member,
                            "channel": before.channel, "guild": before.channel.guild,
                            "bot": self_bot,
                        })
                if before.self_mute != after.self_mute or before.mute != after.mute:
                    await self.event_bus.fire("voice mute", self.name, {
                        "member": member, "user": member,
                        "guild": member.guild, "bot": self_bot,
                    })
                if before.self_deaf != after.self_deaf or before.deaf != after.deaf:
                    await self.event_bus.fire("voice deafen", self.name, {
                        "member": member, "user": member,
                        "guild": member.guild, "bot": self_bot,
                    })

            async def on_guild_role_create(self_bot, role):
                await self.event_bus.fire("role create", self.name, {
                    "role": role, "guild": role.guild, "bot": self_bot,
                })

            async def on_guild_role_delete(self_bot, role):
                await self.event_bus.fire("role delete", self.name, {
                    "role": role, "guild": role.guild, "bot": self_bot,
                })

            async def on_guild_role_update(self_bot, before, after):
                await self.event_bus.fire("role edit", self.name, {
                    "role": after, "guild": after.guild, "bot": self_bot,
                })

            async def on_guild_emojis_update(self_bot, guild, before, after):
                await self.event_bus.fire("guild emoji update", self.name, {
                    "guild": guild, "bot": self_bot,
                })

            async def on_guild_stickers_update(self_bot, guild, before, after):
                await self.event_bus.fire("guild sticker update", self.name, {
                    "guild": guild, "bot": self_bot,
                })

            async def on_guild_update(self_bot, before, after):
                await self.event_bus.fire("guild update", self.name, {
                    "guild": after, "bot": self_bot,
                })

            async def on_invite_create(self_bot, invite):
                await self.event_bus.fire("invite create", self.name, {
                    "invite": invite, "guild": invite.guild, "bot": self_bot,
                })

            async def on_invite_delete(self_bot, invite):
                await self.event_bus.fire("invite delete", self.name, {
                    "invite": invite, "guild": invite.guild, "bot": self_bot,
                })

            async def on_typing(self_bot, channel, user, when):
                if user.bot:
                    return
                await self.event_bus.fire("typing", self.name, {
                    "channel": channel, "user": user,
                    "guild": getattr(channel, 'guild', None), "bot": self_bot,
                })

            async def on_presence_update(self_bot, before, after):
                await self.event_bus.fire("presence update", self.name, {
                    "user": after, "guild": after.guild, "bot": self_bot,
                })

            async def on_interaction(self_bot, interaction):
                if interaction.type == discord.InteractionType.autocomplete:
                    cmd_name = interaction.data.get("name", "") if interaction.data else ""
                    focused = None
                    options = interaction.data.get("options", []) if interaction.data else []
                    stack = list(options)
                    while stack:
                        opt = stack.pop(0)
                        if isinstance(opt, dict):
                            if opt.get("focused", False):
                                focused = opt.get("name", "")
                            if "options" in opt:
                                stack.extend(opt["options"])
                    if cmd_name and focused:
                        await self.event_bus.fire("slash command completion", self.name, {
                            "interaction": interaction,
                            "string": cmd_name,
                            "current argument": focused,
                            "user": interaction.user,
                            "channel": interaction.channel,
                            "guild": interaction.guild,
                            "bot": self_bot,
                        })
                    return
                if interaction.type == discord.InteractionType.application_command:
                    cmd_name = interaction.data.get("name", "") if interaction.data else ""
                    if not self.command_registry.is_tree_command(cmd_name.split()[0]):
                        await self.event_bus.fire("slash command", self.name, {
                            "interaction": interaction,
                            "string": cmd_name,
                            "user": interaction.user,
                            "member": getattr(interaction, 'user', None),
                            "channel": interaction.channel,
                            "guild": interaction.guild,
                            "bot": self_bot,
                        })
                elif interaction.type == discord.InteractionType.component:
                    custom_id = interaction.data.get("custom_id", "") if interaction.data else ""
                    if interaction.data and interaction.data.get("component_type") == 2:
                        await self.event_bus.fire("button click", self.name, {
                            "interaction": interaction,
                            "string": custom_id,
                            "user": interaction.user,
                            "member": getattr(interaction, 'user', None),
                            "channel": interaction.channel,
                            "guild": interaction.guild,
                            "message": interaction.message,
                            "bot": self_bot,
                        })
                    else:
                        comp_type = interaction.data.get("component_type", 0) if interaction.data else 0
                        if comp_type in (3, 5, 6, 7, 8):
                            await self.event_bus.fire("entity dropdown click", self.name, {
                                "interaction": interaction,
                                "string": custom_id,
                                "user": interaction.user,
                                "member": getattr(interaction, 'user', None),
                                "channel": interaction.channel,
                                "guild": interaction.guild,
                                "message": interaction.message,
                                "selected values": interaction.data.get("values", []) if interaction.data else [],
                                "selected entities": interaction.data.get("resolved", {}) if interaction.data else {},
                                "bot": self_bot,
                            })
                        else:
                            await self.event_bus.fire("dropdown click", self.name, {
                                "interaction": interaction,
                                "string": custom_id,
                                "user": interaction.user,
                                "member": getattr(interaction, 'user', None),
                                "channel": interaction.channel,
                                "guild": interaction.guild,
                                "message": interaction.message,
                                "selected values": interaction.data.get("values", []) if interaction.data else [],
                                "bot": self_bot,
                            })
                elif interaction.type == discord.InteractionType.modal_submit:
                    modal_values = self.component_handler.handle_modal_values(interaction, self.runtime)
                    await self.event_bus.fire("modal receive", self.name, {
                        "interaction": interaction,
                        "string": interaction.data.get("custom_id", "") if interaction.data else "",
                        "user": interaction.user,
                        "member": getattr(interaction, 'user', None),
                        "channel": interaction.channel,
                        "guild": interaction.guild,
                        "message": interaction.message,
                        "bot": self_bot,
                        "modal values": modal_values,
                    })

            async def on_guild_available(self_bot, guild):
                await self.event_bus.fire("guild ready", self.name, {
                    "guild": guild, "bot": self_bot,
                })

        return DiscordBotClient(intents=intents)

    async def start_async(self) -> None:
        self.client = self._create_client()
        try:
            self.runtime.bot_instances[self.name] = self.client
            await self.client.start(self.token)
        except Exception as e:
            print(f"[BOT] Error starting {self.name}: {e}")

    def start(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        loop.run_until_complete(self.start_async())

    def start_threaded(self) -> None:
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()

    async def stop_async(self) -> None:
        if self.client:
            await self.client.close()
            self.ready = False

    def stop(self) -> None:
        if self.loop and self.client:
            asyncio.run_coroutine_threadsafe(self.stop_async(), self.loop)


class BotManager:
    def __init__(self, runtime: Runtime, script_manager: ScriptManager):
        self.runtime = runtime
        self.script_manager = script_manager
        self.event_bus = EventBus(runtime)
        self.command_registry = CommandRegistry()
        self.component_handler = ComponentHandler(runtime)
        self.audio_manager = AudioManager()
        self.definitions: list[BotDefinition] = []
        self.instances: dict[str, BotInstance] = {}
        self.config: dict = {}

        runtime.set_bot_manager(self)
        runtime.audio_manager = self.audio_manager

    def register_definition(self, bd: BotDefinition) -> None:
        self.definitions.append(bd)

    def unregister_definition(self, bd: BotDefinition) -> None:
        if bd in self.definitions:
            self.definitions.remove(bd)

    def get_token(self, bot_name: str) -> str | None:
        if bot_name in self.config:
            return self.config[bot_name].get("token")
        for bd in self.definitions:
            if bd.name == bot_name and bd.token:
                return bd.token
        return None

    def build_intents(self, intent_names: list[str]) -> discord.Intents:
        intents = discord.Intents.default()
        for name in intent_names:
            name = str(name).lower().replace(" ", "_")
            if name == "all":
                intents = discord.Intents.all()
            elif name == "default":
                intents = discord.Intents.default()
            elif name == "members":
                intents.members = True
            elif name == "messages":
                intents.messages = True
            elif name == "message_content":
                intents.message_content = True
            elif name == "reactions":
                intents.reactions = True
            elif name == "voice_states":
                intents.voice_states = True
            elif name == "presences":
                intents.presences = True
            elif name == "guilds":
                intents.guilds = True
            elif name == "moderation":
                intents.moderation = True
            elif name == "scheduled_events":
                intents.scheduled_events = True
            elif name == "auto_moderation" or name == "auto_moderation_execution":
                intents.auto_moderation = True
                intents.auto_moderation_execution = True
            elif name == "typing":
                intents.typing = True
            elif name == "dm_messages":
                intents.dm_messages = True
            elif name == "dm_reactions":
                intents.dm_reactions = True
            elif name == "dm_typing":
                intents.dm_typing = True
            elif name == "guild_expressions":
                pass
        return intents

    async def build_instance(self, bd: BotDefinition) -> BotInstance:
        token = self.get_token(bd.name) or bd.token
        if not token:
            raise ValueError(f"No token for bot {bd.name}")
        intents = self.build_intents(bd.intents)
        instance = BotInstance(
            name=bd.name, token=token, intents=intents,
            runtime=self.runtime, event_bus=self.event_bus,
            command_registry=self.command_registry,
            component_handler=self.component_handler,
            audio_manager=self.audio_manager,
        )
        self.instances[bd.name] = instance
        return instance

    def load_config(self, config_path: str = "config.toml") -> None:
        try:
            import tomllib
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        except (ImportError, FileNotFoundError):
            try:
                import toml
                with open(config_path, "r") as f:
                    data = toml.load(f)
            except (ImportError, FileNotFoundError):
                from dotenv import dotenv_values
                env_vals = dotenv_values(".env")
                token = env_vals.get("DISCORD_TOKEN", "")
                if token:
                    self.config["default"] = {"token": token}
                return
        for key, val in data.items():
            if isinstance(val, dict) and "token" in val:
                self.config[key] = val
            elif isinstance(val, str) and key.endswith("_token"):
                self.config[key.replace("_token", "")] = {"token": val}

    async def start_all(self) -> None:
        self.load_config()
        token = self.get_token("default") or self.config.get("default", {}).get("token", "")
        if token:
            bd = BotDefinition()
            bd.name = "default"
            bd.token = token
            bd.intents = ["default", "message_content", "members"]
            instance = await self.build_instance(bd)
            instance.start_threaded()

        for bd in self.definitions:
            if bd.name == "default":
                continue
            instance = await self.build_instance(bd)
            instance.start_threaded()

    async def stop_all(self) -> None:
        for name, instance in self.instances.items():
            instance.stop()

    def get_instance(self, name: str) -> BotInstance | None:
        return self.instances.get(name)

    def get_client(self, name: str) -> discord.Client | None:
        inst = self.instances.get(name)
        return inst.client if inst else None
