from __future__ import annotations
from .parser import Parser, ParseError
from .ast import Script, EventHandler, CommandDecl, SlashCommandDecl, FunctionDecl, BotDefinition
from .runtime import Runtime
from .variable_store import VariableStore
from typing import Any, Optional, Callable
import os
import time
import glob as glob_module


class ScriptFile:
    def __init__(self, path: str, guild_id: str = ""):
        self.path = path
        self.name = os.path.basename(path)
        self.guild_id = guild_id
        self.source = ""
        self.ast: Script | None = None
        self.error: str | None = None
        self.loaded_at: float = 0
        self.last_modified: float = 0
        self.enabled = not self.name.startswith("-")

    def __repr__(self) -> str:
        return f"ScriptFile({self.name}, guild={self.guild_id}, enabled={self.enabled})"


class ScriptManager:
    def __init__(self, runtime: Runtime, script_dir: str = "scripts", variable_store: VariableStore | None = None):
        self.runtime = runtime
        self.script_dir = script_dir
        self.store = variable_store or VariableStore()
        self.scripts: dict[str, ScriptFile] = {}
        self.on_load_callbacks: list[Callable] = []
        self.on_error_callbacks: list[Callable] = []
        os.makedirs(script_dir, exist_ok=True)

    def ensure_guild_dir(self, guild_id: str) -> str:
        path = os.path.join(self.script_dir, guild_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _get_guild_dirs(self) -> list[str]:
        """Return list of guild ID subdirectories under script_dir."""
        dirs = []
        try:
            for entry in os.scandir(self.script_dir):
                if entry.is_dir() and not entry.name.startswith("."):
                    dirs.append(entry.name)
        except FileNotFoundError:
            pass
        return dirs

    def scan(self, guild_id: str = "") -> list[str]:
        if guild_id:
            pattern = os.path.join(self.script_dir, guild_id, "*.discord")
        else:
            pattern = os.path.join(self.script_dir, "**", "*.discord")
        files = glob_module.glob(pattern, recursive=True)
        return [f for f in sorted(files) if os.path.isfile(f)]

    def load_script(self, path: str, guild_id: str = "") -> ScriptFile:
        sf = ScriptFile(path, guild_id)
        try:
            with open(path, "r", encoding="utf-8") as f:
                sf.source = f.read()
            parser = Parser(sf.source, path)
            sf.ast = parser.parse()
            sf.loaded_at = time.time()
            sf.last_modified = os.path.getmtime(path)
            sf.error = None
            self._register_from_ast(sf, guild_id)
        except ParseError as e:
            sf.error = str(e)
            sf.ast = None
            self._report_error(sf, str(e))
        except Exception as e:
            sf.error = f"{type(e).__name__}: {e}"
            sf.ast = None
            self._report_error(sf, sf.error)
        self.scripts[path] = sf
        return sf

    def load_all(self) -> list[ScriptFile]:
        loaded = []
        for guild_id in self._get_guild_dirs():
            for path in self.scan(guild_id):
                sf = self.load_script(path, guild_id)
                loaded.append(sf)
        root_pattern = os.path.join(self.script_dir, "*.discord")
        for path in sorted(glob_module.glob(root_pattern)):
            if os.path.isfile(path):
                sf = self.load_script(path, "__global__")
                loaded.append(sf)
        return loaded

    def reload_script(self, path: str) -> ScriptFile:
        old = self.scripts.get(path)
        if old and old.ast:
            self._unregister_from_ast(old)
        sf = self.load_script(path, old.guild_id if old else "")
        self._fire_on_load(sf)
        return sf

    def reload_all(self) -> list[ScriptFile]:
        for guild_id in list(self.runtime.guild_functions.keys()):
            self.runtime.guild_functions[guild_id].clear()
            self.runtime.guild_event_handlers[guild_id].clear()
            self.runtime.guild_registered_commands[guild_id].clear()
            self.runtime.guild_slash_commands[guild_id].clear()
            self.runtime.guild_custom_event_handlers[guild_id].clear()
            self.runtime.guild_embed_templates[guild_id].clear()
        self.runtime.guild_functions.clear()
        self.runtime.guild_event_handlers.clear()
        self.runtime.guild_registered_commands.clear()
        self.runtime.guild_slash_commands.clear()
        self.runtime.guild_custom_event_handlers.clear()
        self.runtime.guild_embed_templates.clear()
        return self.load_all()

    def get_script(self, name: str) -> ScriptFile | None:
        for path, sf in self.scripts.items():
            if sf.name == name or sf.name == f"{name}.discord" or path == name:
                return sf
        for path, sf in self.scripts.items():
            if name in path:
                return sf
        return None

    def _register_from_ast(self, sf: ScriptFile, guild_id: str = "") -> None:
        if not sf.ast:
            return
        if not sf.enabled:
            return
        gid = guild_id or "__global__"

        if gid not in self.runtime.guild_functions:
            self.runtime.guild_functions[gid] = {}
            self.runtime.guild_event_handlers[gid] = []
            self.runtime.guild_registered_commands[gid] = []
            self.runtime.guild_slash_commands[gid] = []
            self.runtime.guild_custom_event_handlers[gid] = {}
            self.runtime.guild_embed_templates[gid] = {}

        for key, val in sf.ast.options.items():
            self.runtime.option_vars[key] = val
        for name, fn in sf.ast.functions.items():
            self.runtime.guild_functions[gid][name] = fn
        for cmd in sf.ast.commands:
            self.runtime.guild_registered_commands[gid].append(cmd)
        for sc in sf.ast.slash_commands:
            self.runtime.guild_slash_commands[gid].append(sc)
        for ev in sf.ast.events:
            self.runtime.guild_event_handlers[gid].append(ev)
            if ev.event_type == "custom event":
                filter_text = ev.filters.get("type", "")
                if filter_text not in self.runtime.guild_custom_event_handlers[gid]:
                    self.runtime.guild_custom_event_handlers[gid][filter_text] = []
                self.runtime.guild_custom_event_handlers[gid][filter_text].append(ev)
        for bd in sf.ast.bot_definitions:
            if self.runtime.bot_manager:
                self.runtime.bot_manager.register_definition(bd)

    def _unregister_from_ast(self, sf: ScriptFile) -> None:
        if not sf.ast:
            return
        gid = sf.guild_id or "__global__"
        for name in sf.ast.functions:
            self.runtime.guild_functions.get(gid, {}).pop(name, None)
        for cmd in sf.ast.commands:
            cmds = self.runtime.guild_registered_commands.get(gid, [])
            if cmd in cmds:
                cmds.remove(cmd)
        for sc in sf.ast.slash_commands:
            scmds = self.runtime.guild_slash_commands.get(gid, [])
            if sc in scmds:
                scmds.remove(sc)
        for ev in sf.ast.events:
            handlers = self.runtime.guild_event_handlers.get(gid, [])
            if ev in handlers:
                handlers.remove(ev)
        for bd in sf.ast.bot_definitions:
            if self.runtime.bot_manager:
                self.runtime.bot_manager.unregister_definition(bd)

    def _report_error(self, sf: ScriptFile, msg: str) -> None:
        print(f"[ERROR] File: {sf.path}: {msg}")
        for cb in self.on_error_callbacks:
            try:
                cb(sf, msg)
            except Exception:
                pass
        try:
            bus = self.runtime.bot_manager.event_bus
            if bus:
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    if loop and loop.is_running():
                        asyncio.ensure_future(bus.fire("script error", "", {
                            "script": sf.name,
                            "error": msg,
                            "file": sf.path,
                        }))
                except RuntimeError:
                    pass
        except Exception:
            pass

    def _fire_on_load(self, sf: ScriptFile) -> None:
        for cb in self.on_load_callbacks:
            try:
                cb(sf)
            except Exception:
                pass

    def get_summary(self) -> list[dict[str, Any]]:
        summary = []
        for path, sf in self.scripts.items():
            info = {
                "name": sf.name,
                "path": path,
                "guild_id": sf.guild_id,
                "enabled": sf.enabled,
                "loaded": sf.ast is not None,
                "error": sf.error,
                "functions": [],
                "commands": [],
                "events": [],
                "bot_definitions": [],
            }
            if sf.ast:
                info["functions"] = list(sf.ast.functions.keys())
                info["commands"] = [c.name for c in sf.ast.commands]
                info["events"] = [e.event_type for e in sf.ast.events]
                info["bot_definitions"] = [b.name for b in sf.ast.bot_definitions]
            summary.append(info)
        return summary