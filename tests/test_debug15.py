from language.parser import Parser
import sys

files = [
    "scripts/example.discord",
    "scripts/example1_moderation.discord",
    "scripts/example2_embeds.discord",
    "scripts/example3_components.discord",
    "scripts/example4_events.discord",
    "scripts/example5_variables.discord",
    "scripts/example6_music.discord",
    "scripts/example7_slash.discord",
]

for fp in files:
    try:
        with open(fp, "r", encoding="utf-8") as f:
            source = f.read()
        parser = Parser(source)
        script = parser.parse()
        print(f"OK  {fp}: {len(script.events)} events, {len(script.commands)} commands, {len(script.bot_definitions)} bots")
    except Exception as e:
        print(f"FAIL {fp}: {e}")
    sys.stdout.flush()
