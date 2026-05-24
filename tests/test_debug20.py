from language.parser import Parser

with open("scripts/example.discord", "r", encoding="utf-8") as f:
    source = f.read()

parser = Parser(source)
try:
    script = parser.parse()
    print(f"OK: {len(script.events)} events, {len(script.commands)} commands")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
