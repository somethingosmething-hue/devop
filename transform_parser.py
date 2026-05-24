# Transform parse_statement to use single return point
with open("language/parser.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find parse_statement boundaries
start = None
end = None
for i, line in enumerate(lines):
    if "def parse_statement" in line:
        start = i
    elif start is not None and line.strip().startswith("def ") and i > start:
        end = i - 1
        break

if end is None:
    end = len(lines) - 1

print(f"parse_statement: lines {start+1} to {end+1}")

# Add stmt variable initialization right after the first line
# Change `return None` to `stmt = None` and all other `return X` to `stmt = X`
modified = 0
for i in range(start, end + 1):
    line = lines[i]
    stripped = line.strip()
    if stripped.startswith("return "):
        # Don't modify returns inside nested string literals
        indent = line[:len(line) - len(line.lstrip())]
        expr = stripped[7:]  # after "return "
        lines[i] = f"{indent}_pv = {expr}\n"
        modified += 1

# Add `return _pv` at the end, before the blank line or end of method
# Find a good place to insert: after the last statement, before the next method
# The last line of parse_statement should be the last return or the end
last_line = end
# Check if we need to add `return _pv`
for i in range(end, start - 1, -1):
    stripped = lines[i].strip()
    if stripped.startswith("_pv = ") or stripped.startswith("return"):
        # Add return after this line
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        # Insert after this line
        lines.insert(i + 1, f"{indent}return _pv\n")
        break

print(f"Modified {modified} return statements")

with open("language/parser.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Done!")
