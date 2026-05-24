from language.lexer import Lexer

ex1 = """options:
    prefix: "!"

on script load:
    send "&aModeration script loaded!" to console

discord command kick [<member>]:
    prefixes: !
    permissions: kick_members
    permission message: "You don't have permission to kick members!"
    trigger:
        if arg-1 is not set:
            reply with "Usage: !kick <member>"
            stop
        kick arg-1 due to "Kicked by moderator"
        reply with "%mention tag of arg-1% has been kicked!"
"""

lexer = Lexer(ex1)
tokens = lexer.tokenize()
# Find tokens around line 7
for i, t in enumerate(tokens):
    if 6 <= t.line <= 8:
        print(f"  [{i:3d}] {t.type.name:15s} {str(t.value)[:40]:40s} L{t.line}:{t.column}")
