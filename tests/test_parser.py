from language.parser import Parser
from language.ast import *

with open("scripts/example.discord", "r") as f:
    source = f.read()

print("=== PARSING ===")
parser = Parser(source)
script = parser.parse()

print(f"Functions: {list(script.functions.keys())}")
print(f"Commands: {[c.name for c in script.commands]}")
for c in script.commands:
    print(f"  - {c.name}: {len(c.trigger)} trigger statements")
    for stmt in c.trigger:
        print(f"    {type(stmt).__name__}: {stmt.__dict__ if hasattr(stmt, '__dict__') else ''}")

print(f"\nEvents: {[e.event_type for e in script.events]}")
for e in script.events:
    print(f"  - {e.event_type}: {len(e.body)} body statements")
    for stmt in e.body:
        print(f"    {type(stmt).__name__}")

print(f"\nOptions: {script.options}")
print(f"Bot defs: {[b.name for b in script.bot_definitions]}")

print("\n=== PARSING: Example 1 (Moderation) ===")
ex1 = """options:
    prefix: "!"

on script load:
    send "&aModeration script loaded!" to console

discord command kick [<member>]:
    prefixes: !
    permissions: kick_members
    permission message: "You don't have permission to kick members!"
    trigger:
        if arg-1 is not set:
            reply with "Usage: !kick <member>"
            stop
        kick arg-1 due to "Kicked by moderator"
        reply with "%mention tag of arg-1% has been kicked!"
"""
p1 = Parser(ex1)
s1 = p1.parse()
print(f"Commands: {[c.name for c in s1.commands]}")
print(f"Events: {[e.event_type for e in s1.events]}")
print("OK!")

print("\n=== ALL PARSER TESTS PASSED ===")
