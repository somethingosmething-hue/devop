from language.lexer import Lexer

source = """options:
    prefix: "!"
"""

print("=== SOURCE ===")
print(repr(source))
print()

lexer = Lexer(source)
tokens = lexer.tokenize()
print("=== TOKENS ===")
for i, t in enumerate(tokens):
    print(f"  [{i:3d}] {t.type.name:15s} {str(t.value)[:40]:40s} L{t.line}:{t.column}")

from language.parser import Parser
parser = Parser(source)
print(f"\nParser pos before: {parser.peek()}")
script = parser.parse()
print(f"Options: {script.options}")
print("SUCCESS!")
