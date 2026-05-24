from language.lexer import Lexer, TokenType
from language.parser import Parser

# Monkey-patch for debugging
original_parse_send = Parser.parse_send_effect
def debug_parse_send(self):
    print(f"  parse_send_effect called, peek={self.peek().type.name} '{self.peek().value}' pos={self.pos}")
    result = original_parse_send(self)
    print(f"  parse_send_effect returning, peek={self.peek().type.name} '{self.peek().value}' pos={self.pos}")
    return result
Parser.parse_send_effect = debug_parse_send

original_parse_statement = Parser.parse_statement
def debug_parse_statement(self):
    print(f"parse_statement called, peek={self.peek().type.name} '{self.peek().value}' pos={self.pos}")
    result = original_parse_statement(self)
    print(f"parse_statement returning {type(result).__name__}, peek={self.peek().type.name} '{self.peek().value}' pos={self.pos}")
    return result
Parser.parse_statement = debug_parse_statement

source = """options:
    prefix: "!"

on script load:
    send "hello" to console
"""

parser = Parser(source)
script = parser.parse()
print(f"OK: {len(script.events)} events")
