from __future__ import annotations
from .parser import Parser, ParseError
from .ast import Script, EventHandler, CommandDecl, SlashCommandDecl, FunctionDecl, BotDefinition
from .runtime import Runtime
from .variable_store import VariableStore
from typing import Any, Optional, Callable
import os
import time
import threading
import glob as glob_module


class ScriptFile:
    def __init__(self, path: str):
        self.path = path
        self.name = os.path.basename(path)
        self.source = ""
        self.ast: Script | None = None
        self.error: str | None = None
        self.loaded_at: float = 0
        self.last_modified: float = 0
        self.enabled = not self.name.startswith("-")

    def __repr__(self) -> str:
        return f"ScriptFile({self.name}, enabled={self.enabled})"


class ScriptManager:
    def __init__(self, runtime: Runtime, script_dir: str = "scripts", variable_store: VariableStore | None = None):
        self.runtime = runtime
        self.script_dir = script_dir
        self.store = variable_store or VariableStore()
        self.scripts: dict[str, ScriptFile] = {}
        self.on_load_callbacks: list[Callable] = []
        self.on_error_callbacks: list[Callable] = []
        self._watching = False
        self._watch_thread: threading.Thread | None = None
        self._running = True
        os.makedirs(script_dir, exist_ok=True)

    def scan(self) -> list[str]:
        pattern = os.path.join(self.script_dir, "**", "*.discord")
        files = glob_module.glob(pattern, recursive=True)
        return [f for f in sorted(files) if os.path.isfile(f)]

    def load_script(self, path: str) -> ScriptFile:
        sf = ScriptFile(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                sf.source = f.read()
            parser = Parser(sf.source, path)
            sf.ast = parser.parse()
            sf.loaded_at = time.time()
            sf.last_modified = os.path.getmtime(path)
            sf.error = None
            self._register_from_ast(sf)
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
        for path in self.scan():
            sf = self.load_script(path)
            loaded.append(sf)
        return loaded

    def reload_script(self, path: str) -> ScriptFile:
        old = self.scripts.get(path)
        if old and old.ast:
            self._unregister_from_ast(old)
        sf = self.load_script(path)
        self._fire_on_load(sf)
        return sf

    def reload_all(self) -> list[ScriptFile]:
        self.runtime.functions.clear()
        self.runtime.event_handlers.clear()
        self.runtime.registered_commands.clear()
        self.runtime.slash_commands.clear()
        self.runtime.embed_templates.clear()
        self.runtime.custom_event_handlers.clear()
        return self.load_all()

    def get_script(self, name: str) -> ScriptFile | None:
        for path, sf in self.scripts.items():
            if sf.name == name or sf.name == f"{name}.discord" or path == name:
                return sf
        for path, sf in self.scripts.items():
            if name in path:
                return sf
        return None

    def _register_from_ast(self, sf: ScriptFile) -> None:
        if not sf.ast:
            return
        if sf.enabled:
            for name, fn in sf.ast.functions.items():
                self.runtime.functions[name] = fn
            for cmd in sf.ast.commands:
                self.runtime.registered_commands.append(cmd)
            for sc in sf.ast.slash_commands:
                self.runtime.slash_commands.append(sc)
            for ev in sf.ast.events:
                self.runtime.event_handlers.append(ev)
                if ev.event_type == "custom event":
                    filter_text = ev.filters.get("type", "")
                    if filter_text not in self.runtime.custom_event_handlers:
                        self.runtime.custom_event_handlers[filter_text] = []
                    self.runtime.custom_event_handlers[filter_text].append(ev)
            for bd in sf.ast.bot_definitions:
                if self.runtime.bot_manager:
                    self.runtime.bot_manager.register_definition(bd)

    def _unregister_from_ast(self, sf: ScriptFile) -> None:
        if not sf.ast:
            return
        for name in sf.ast.functions:
            self.runtime.functions.pop(name, None)
        for cmd in sf.ast.commands:
            if cmd in self.runtime.registered_commands:
                self.runtime.registered_commands.remove(cmd)
        for sc in sf.ast.slash_commands:
            if sc in self.runtime.slash_commands:
                self.runtime.slash_commands.remove(sc)
        for ev in sf.ast.events:
            if ev in self.runtime.event_handlers:
                self.runtime.event_handlers.remove(ev)
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

    def start_watching(self, interval: float = 1.0) -> None:
        if self._watching:
            return
        self._watching = True
        self._running = True

        def watch_loop():
            last_states: dict[str, float] = {}
            for path, sf in self.scripts.items():
                try:
                    last_states[path] = os.path.getmtime(path)
                except OSError:
                    pass
            while self._running:
                time.sleep(interval)
                for path in self.scan():
                    try:
                        mtime = os.path.getmtime(path)
                        if path not in last_states:
                            last_states[path] = mtime
                            self.reload_script(path)
                        elif mtime > last_states[path]:
                            last_states[path] = mtime
                            print(f"[WATCH] Detected change in {path}, reloading...")
                            self.reload_script(path)
                    except OSError:
                        pass

        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()

    def stop_watching(self) -> None:
        self._running = False
        self._watching = False

    def get_summary(self) -> list[dict[str, Any]]:
        summary = []
        for path, sf in self.scripts.items():
            info = {
                "name": sf.name,
                "path": path,
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
