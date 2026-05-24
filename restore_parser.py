# Restore parser.py to working state
# We'll rewrite with only the safe changes

with open("language/parser.py", "r", encoding="utf-8") as f:
    content = f.read()

# Strategy: find parse_statement body and revert it to original return-based style
# while keeping the other changes (maybe_parse_bot_clause, parse_send_effect, etc.)

# Find relevant sections
import re

# The original parse_statement should return directly from branches
# The transformed version uses _pv
# Let's find the transformed method and revert it

lines = content.split('\n')

# Find parse_statement
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('def parse_statement'):
        start_idx = i
    elif start_idx and line.strip().startswith('def ') and i > start_idx:
        end_idx = i - 1
        break

if start_idx and not end_idx:
    end_idx = len(lines) - 1

print(f"parse_statement: lines {start_idx+1} to {end_idx+1}")

# Check the last few lines before the next method
for i in range(end_idx, max(start_idx, end_idx - 10) - 1, -1):
    print(f"  L{i+1}: {lines[i][:80]}")
