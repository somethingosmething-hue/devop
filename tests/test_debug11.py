from language.parser import Parser

# Very simple test - no components
source = """discord command test:
    prefixes: !
    trigger:
        reply with "hello"
"""

parser = Parser(source)
print("Parsing simple reply...")
script = parser.parse()
print(f"OK: {len(script.events)} events, {len(script.commands)} commands")
