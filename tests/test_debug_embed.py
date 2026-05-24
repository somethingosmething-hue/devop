from language.lexer import Lexer, TokenType

source = """options:
    prefix: "!"

discord command info:
    prefixes: !
    trigger:
        make embed:
            set title of embed to "Server Info"
            set description of embed to "Information about this server"
            set color of embed to #2ECC71
            set footer of embed to "Requested by %display name of event-author%"
        post last embed to event-channel
"""

lexer = Lexer(source)
tokens = lexer.tokenize()
for i, t in enumerate(tokens):
    if 8 <= t.line <= 14:
        print(f"[{i:3d}] {t.type.name:20s} {str(t.value)[:50]:50s} L{t.line}:{t.column}")
