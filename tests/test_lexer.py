from language.lexer import Lexer

source = """options:
    prefix: "!"

on script load:
    send "&aExample script loaded!" to console
"""

print("=== SOURCE ===")
print(source)
print("=== TOKENS ===")
lexer = Lexer(source)
tokens = lexer.tokenize()
for t in tokens:
    print(f"  {t.type.name:15s} {str(t.value)[:40]:40s} L{t.line}:{t.column}")
