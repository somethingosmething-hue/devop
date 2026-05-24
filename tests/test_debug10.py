from language.parser import Parser

source = """discord command menu:
    prefixes: !
    trigger:
        make row:
            add new button primary with id "help" named "Help" to components of row builder
"""

parser = Parser(source)
print("Parsing...")
script = parser.parse()
print(f"OK: {len(script.events)} events, {len(script.commands)} commands")
