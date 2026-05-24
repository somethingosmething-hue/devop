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

try:
    lexer = Lexer(ex1)
    tokens = lexer.tokenize()
    print(f"Tokenized OK: {len(tokens)} tokens")
except Exception as e:
    print(f"Error at pos={lexer.pos}, line={lexer.line}, col={lexer.column}")
    print(f"Context: {repr(ex1[max(0,lexer.pos-20):lexer.pos+20])}")
    print(f"Char: {repr(lexer.peek())}")
    import traceback
    traceback.print_exc()
