from language.parser import Parser

fp = "scripts/example.discord"
with open(fp, "r", encoding="utf-8") as f:
    source = f.read()
print(f"Source length: {len(source)} chars")
print("---SOURCE---")
print(source[:500])
print("---END---")
parser = Parser(source)
print("Parsing...")
script = parser.parse()
print(f"OK ({len(script.events)} events, {len(script.commands)} commands)")
