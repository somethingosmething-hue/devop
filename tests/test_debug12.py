from language.lexer import Lexer
from language.parser import Parser

source = """discord command test:
    prefixes: !
    trigger:
        make row:
            add new button primary with id "help" named "Help" to components of row builder
"""

lexer = Lexer(source)
tokens = lexer.tokenize()
print(f"Tokens: {len(tokens)}")
for i, t in enumerate(tokens):
    print(f"[{i}] {t.type.name} {t.value}")

# Now parse, with step tracing
import traceback
try:
    parser = Parser(source)
    print("\nParser created, calling parse...")
    script = parser.parse()
    print(f"OK: {len(script.events)} events, {len(script.commands)} commands")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
