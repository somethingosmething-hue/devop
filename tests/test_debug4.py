from language.parser import Parser, TokenType

source = """options:
    prefix: "!"
"""

parser = Parser(source)

# Simulate what parse() does before calling parse_options_block
parser.pos = 0
parser.skip_newlines()
print(f"After skip_newlines: pos={parser.pos}, peek={parser.peek()}")
parser.advance()  # consume "options" keyword
print(f"After advance: pos={parser.pos}, peek={parser.peek()}")
parser.expect(TokenType.COLON)
print(f"After COLON: pos={parser.pos}, peek={parser.peek()}")
parser.skip_newlines()
print(f"After skip_newlines: pos={parser.pos}, peek={parser.peek()}")

# Now we're in parse_options_block
print(f"\nCalling parse_options_block...")
# Manually step through:
t = parser.peek()
print(f"  peek type = {t.type.name}, value = {t.value}")
parser.advance()  # consume INDENT
print(f"  after INDENT consume: pos={parser.pos}")
t = parser.peek()
print(f"  next token: {t.type.name} {t.value}")
parser.advance()  # consume IDENTIFIER "prefix"
print(f"  after IDENTIFIER: pos={parser.pos}")
parser.expect(TokenType.COLON)
print(f"  after COLON: pos={parser.pos}")
parser.skip_newlines()
print(f"  after skip_newlines: pos={parser.pos}")

# NOW try parse_expression
t = parser.tokens[parser.pos]
print(f"  About to parse_expression, token = {t.type.name} {t.value} L{t.line}:{t.column}")

# Step through parse_primary manually
from language.ast import StringLiteral
tok = parser.peek()
print(f"  parse_primary sees: {tok.type.name} {tok.value}")
if tok.type == TokenType.STRING:
    parser.advance()
    val = StringLiteral(value=tok.value, line=tok.line, column=tok.column)
    print(f"  Parsed StringLiteral: {val.value}")
else:
    print(f"  NOT a STRING!")
    print(f"  Checking: tok.type = {tok.type}, TokenType.STRING = {TokenType.STRING}")
    print(f"  tok.type == TokenType.STRING: {tok.type == TokenType.STRING}")
