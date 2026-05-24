from language.parser import Parser

source = """options:
    prefix: "!"

discord command menu:
    prefixes: !
    trigger:
        make embed:
            set title of embed to "Interactive Menu"
            set description of embed to "Click a button below!"
            set color of embed to #E91E63
        make row:
            add new button primary with id "help" named "Help" to components of row builder
            add new button success with id "greet" named "Greet" to components of row builder
        post last embed to event-channel
"""

parser = Parser(source)
print("Parsing...")
script = parser.parse()
print(f"OK: {len(script.events)} events, {len(script.commands)} commands")
