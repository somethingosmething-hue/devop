from language.parser import Parser

source = """options:
    prefix: "!"

on script load:
    send "hello" to console
"""

parser = Parser(source)
script = parser.parse()
print(f"OK: {len(script.events)} events")
