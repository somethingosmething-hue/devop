from language.lexer import Lexer

source = "options:\n    prefix: \"!\"\n"
print("Tokenizing...")
lexer = Lexer(source)
try:
    tokens = lexer.tokenize()
    print(f"Got {len(tokens)} tokens")
    for t in tokens:
        print(f"  {t.type.name}: {t.value}")
except Exception as e:
    print(f"Error: {e}")
