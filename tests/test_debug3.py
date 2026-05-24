from language.parser import Parser, TokenType

source = """options:
    prefix: "!"
"""

parser = Parser(source)
for i, t in enumerate(parser.tokens):
    print(f"  Token[{i}] = {t.type.name:12s} {str(t.value)[:30]:30s}")

parser.pos = 4  # KEYWORD "prefix"
print(f"\nSimulating from pos=4 (after INDENT consumed):")
print(f"  peek = {parser.peek()}")
# Option names can be either IDENTIFIER or KEYWORD
parser.expect(TokenType.KEYWORD)
print(f"  after KEYWORD, peek = {parser.peek()}")
parser.expect(TokenType.COLON)
print(f"  after COLON, peek = {parser.peek()}")
parser.skip_newlines()
print(f"  after skip_newlines, peek = {parser.peek()}")
val = parser.parse_expression()
print(f"  parsed value = {val}")
