from language.runtime import Runtime
from language.types import TypeRegistry
from language.variable_store import VariableStore
from language.script_manager import ScriptManager
from language.builtins.effects import register_effects
from language.builtins.expressions import register_expressions
from language.builtins.conditions import register_conditions
from language.diagnostic_commands import register_diagnostic_commands
from bot.manager import BotManager
import asyncio
import signal
import sys
import os


def main(config_path: str = "config.toml"):
    type_registry = TypeRegistry()
    runtime = Runtime(type_registry)

    register_effects(runtime)
    register_expressions(runtime)
    register_conditions(runtime)
    register_diagnostic_commands(runtime)

    store = VariableStore("data/variables.json")
    store.load()

    for key, val in store.get_all().items():
        runtime.global_scope.set(key, val)

    script_manager = ScriptManager(runtime, "scripts", store)
    bot_manager = BotManager(runtime, script_manager)
    bot_manager.load_config(config_path)

    script_manager.on_error_callbacks.append(
        lambda sf, err: print(f"[SCRIPT ERROR] {sf.name}: {err}")
    )

    loaded = script_manager.load_all()
    print(f"[MAIN] Loaded {len(loaded)} scripts for {len(set(sf.guild_id for sf in loaded))} guild(s)")

    shutdown_event = asyncio.Event()

    def _signal_handler():
        shutdown_event.set()

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _signal_handler)
            except NotImplementedError:
                pass

        loop.run_until_complete(_run_bots(bot_manager, shutdown_event))
    except KeyboardInterrupt:
        pass
    finally:
        print("[MAIN] Shutting down...")
        try:
            loop.run_until_complete(bot_manager.stop_all())
        except Exception:
            pass
        store.save()
        print("[MAIN] Variables saved. Goodbye!")


async def _run_bots(bot_manager: BotManager, shutdown: asyncio.Event):
    await bot_manager.start_all()

    if bot_manager.instances:
        print(f"[MAIN] {len(bot_manager.instances)} bot(s) running. Press Ctrl+C to stop.")
        await shutdown.wait()
    else:
        print("[MAIN] No bots configured. Running in script-only mode.")
        print("[MAIN] Use Ctrl+C to exit.")
        await shutdown.wait()


if __name__ == "__main__":
    main()
