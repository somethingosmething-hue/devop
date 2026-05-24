from language.parser import Parser

source = """options:
    prefix: "!"
"""

parser = Parser(source)
try:
    script = parser.parse()
    print(f"OK: {script.options}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
