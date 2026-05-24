from language.parser import Parser
from language.lexer import Lexer
import os, glob

passed = 0
failed = 0

script_dir = "scripts"
for fp in sorted(glob.glob(os.path.join(script_dir, "*.discord"))):
    name = os.path.basename(fp)
    try:
        with open(fp, "r", encoding="utf-8") as f:
            source = f.read()
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(source)
        script = parser.parse()
        ev = len(script.events)
        cm = len(script.commands)
        fn = len(script.functions)
        bo = len(script.bot_definitions)
        print(f"  OK  {name}: {ev} events, {cm} commands, {fn} funcs, {bo} bots")
        passed += 1
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        failed += 1

print(f"\n{passed} passed, {failed} failed")
