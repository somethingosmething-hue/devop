# Undo parse_statement transformation
import re

with open("language/parser.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the parse_statement method
start_marker = "def parse_statement(self) -> Statement | None:"
end_marker = "\n    def parse_"

start = content.find(start_marker)
end = content.find(end_marker, start)

if start == -1 or end == -1:
    print("Could not find boundaries")
    exit(1)

# Extract the method body
body = content[start:end]
print(f"Method body: {len(body)} chars")

# Count _pv usage
pv_count = body.count("_pv = ")
print(f"_pv = occurrences: {pv_count}")
return_count = body.count("return ")
print(f"return occurrences: {return_count}")

# Check if the method has been transformed
if "_pv = None" in body and "return _pv" in body:
    print("Method IS transformed")
else:
    print("Method is NOT transformed (already original)")
