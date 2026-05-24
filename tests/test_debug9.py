from language.lexer import Lexer, TokenType

source = """discord command menu:
    prefixes: !
    trigger:
        make row:
            add new button primary with id "help" named "Help" to components of row builder
"""

lexer = Lexer(source)
tokens = lexer.tokenize()
for i, t in enumerate(tokens):
    print(f"[{i:3d}] {t.type.name:20s} {str(t.value)[:40]:40s} L{t.line}:{t.column}")
