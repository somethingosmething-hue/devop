from language.lexer import Lexer

with open("scripts/example.discord", "r") as f:
    source = f.read()

print("=== ALL TOKENS ===")
lexer = Lexer(source)
tokens = lexer.tokenize()
for i, t in enumerate(tokens):
    print(f"  [{i:3d}] {t.type.name:15s} {str(t.value)[:40]:40s} L{t.line}:{t.column}")
