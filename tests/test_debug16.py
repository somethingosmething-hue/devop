from language.lexer import Lexer, TokenType

with open("scripts/example6_music.discord", "r", encoding="utf-8") as f:
    source = f.read()

lexer = Lexer(source)
tokens = lexer.tokenize()
for i, t in enumerate(tokens):
    print(f"[{i:3d}] {t.type.name:20s} {str(t.value)[:50]:50s} L{t.line}:{t.column}")
