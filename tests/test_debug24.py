import traceback
from language.parser import Parser
from language.lexer import Lexer, TokenType

source = """options:
    prefix: "!"

on script load:
    send "hello" to console
"""

# First check tokens
lexer = Lexer(source)
tokens = lexer.tokenize()
print("Tokens:")
for i, t in enumerate(tokens):
    print(f"  [{i}] {t.type.name:20s} {t.value!r:40s} L{t.line}:{t.column}")

# Now parse
parser = Parser(source)
try:
    script = parser.parse()
    print(f"OK: {len(script.events)} events")
except Exception as e:
    traceback.print_exc()
    tok = parser.peek()
    print(f"Peek at error: {tok.type.name} {tok.value!r} L{tok.line}:{tok.column}")
    print(f"Parser pos: {parser.pos}")
    # Print remaining tokens
    print("Remaining tokens:")
    for i in range(parser.pos, min(parser.pos + 5, len(parser.tokens))):
        t = parser.tokens[i]
        print(f"  [{i}] {t.type.name:20s} {t.value!r:40s} L{t.line}:{t.column}")
