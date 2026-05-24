from language.parser import Parser
import sys

with open("scripts/example6_music.discord", "r", encoding="utf-8") as f:
    source = f.read()

# Add debugging to the parser
from language import parser as parser_module
original_parse_statement = parser_module.Parser.parse_statement
original_skip_newlines = parser_module.Parser.skip_newlines

def debug_parse_statement(self):
    result = original_parse_statement(self)
    tok = self.peek()
    # Print current position
    print(f"parse_statement -> {result.__class__.__name__ if result else 'None'} | peek: {tok.type.name} '{tok.value}' L{tok.line}:{tok.column}", flush=True)
    return result

original_parse_block = parser_module.Parser.parse_block
def debug_parse_block(self):
    print("=== parse_block START ===", flush=True)
    body = original_parse_block(self)
    print("=== parse_block END ===", flush=True)
    return body

parser_module.Parser.parse_block = debug_parse_block
parser_module.Parser.parse_statement = debug_parse_statement

parser = Parser(source)
script = parser.parse()
print(f"OK: {len(script.events)} events, {len(script.commands)} commands")
