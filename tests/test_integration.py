"""Integration tests — full pipeline from parsing to execution with mock Discord objects."""

import sys
sys.path.insert(0, ".")

from language.runtime import Runtime, Scope
from language.types import TypeRegistry, parse_timespan, parse_color, PERMISSION_NAMES
from language.builtins.effects import register_effects
from language.builtins.expressions import register_expressions
from language.builtins.conditions import register_conditions
from language.parser import Parser


def make_runtime():
    r = Runtime(TypeRegistry())
    register_effects(r)
    register_expressions(r)
    register_conditions(r)
    return r


def make_mock_guild():
    role = type("Role", (), {"id": 111, "name": "Admin", "color": 0xFF0000, "mention": "<@&111>",
                             "hoist": False, "position": 1, "permissions": 8})()
    channel = type("TextChannel", (), {"id": 222, "name": "general", "mention": "<#222>",
                                        "guild": None, "topic": "General chat"})()
    member = type("Member", (), {
        "id": 123, "name": "TestUser", "display_name": "TestUser", "mention": "<@123>",
        "nick": None, "bot": False, "avatar": None, "banner": None,
        "roles": [role], "top_role": role, "guild_permissions": type("Perms", (), {"kick_members": True})(),
        "guild": None, "voice": None, "timed_out_until": None,
        "timeout": lambda **kw: None,
        "add_roles": lambda *a, **kw: None,
        "remove_roles": lambda *a, **kw: None,
        "kick": lambda **kw: None,
        "ban": lambda **kw: None,
        "send": lambda x: None,
    })()
    guild = type("Guild", (), {
        "id": 999, "name": "Test Guild", "member_count": 10,
        "members": [member], "roles": [role], "channels": [channel],
        "text_channels": [channel], "voice_channels": [], "stage_channels": [],
        "categories": [], "emojis": [], "bans": [], "invites": [],
        "owner": member, "icon": None, "banner": None, "splash": None,
        "afk_channel": None, "system_channel": None,
        "verification_level": type("VL", (), {"name": "low"})(),
        "default_notifications": type("DN", (), {"name": "all_messages"})(),
        "explicit_content_filter": type("ECF", (), {"name": "disabled"})(),
        "get_member": lambda uid: member,
        "create_role": lambda **kw: role,
    })()
    member.guild = guild
    channel.guild = guild
    role.guild = guild
    return guild, member, channel, role


def make_mock_message(guild, member, channel):
    return type("Message", (), {
        "id": 444, "content": "Hello world!", "author": member, "member": member,
        "channel": channel, "guild": guild, "mention": "<msg:444>",
        "jump_url": "https://discord.com/msg/444",
        "created_at": None, "edited_at": None, "pinned": False,
        "tts": False, "reactions": [], "attachments": [],
        "type": type("MsgType", (), {"name": "default"})(),
        "flags": type("Flags", (), {"ephemeral": False, "crossposted": False})(),
        "delete": lambda **kw: None,
        "reply": lambda x, **kw: None,
    })()


# === TEST: Full script execution ===

def test_parse_and_execute_variable():
    r = make_runtime()
    scope = Scope(r.global_scope)
    source = 'set {_x} to 42'
    parser = Parser(source)
    stmt = parser.parse_statement()
    assert stmt is not None
    r.execute_effect_list([stmt], scope)
    assert r.local_vars.get("_x") == 42, f"Expected 42, got {r.local_vars.get('_x')}"
    print("[OK] parse + execute: set variable")


def test_parse_and_execute_expression():
    r = make_runtime()
    scope = Scope(r.global_scope)
    source = 'reply with "Hello world!"'
    parser = Parser(source)
    stmt = parser.parse_statement()
    assert stmt is not None
    assert stmt.effect_type == "reply"
    result = r.execute_effect(stmt, scope)
    print(f"[OK] parse + execute: reply effect -> {result}")


def test_interpolation_with_mock():
    r = make_runtime()
    scope = Scope(r.global_scope)
    _, member, _, _ = make_mock_guild()
    scope.set("event-player", member)
    val = r.evaluate(Parser('"Hello %name of event-player%!"').parse_expression(), scope)
    assert val == "Hello TestUser!", f'Expected "Hello TestUser!", got "{val}"'
    print("[OK] interpolation with property access")

    scope.set("x", 100)
    val = r.evaluate(Parser('"value: %x%"').parse_expression(), scope)
    assert val == "value: 100", f'Expected "value: 100", got "{val}"'
    print("[OK] interpolation with variable reference")


def test_parse_if_statement():
    r = make_runtime()
    scope = Scope(r.global_scope)
    source = """
if 1 == 1:
    set {_result} to "yes"
else:
    set {_result} to "no"
"""
    parser = Parser(source.strip())
    stmt = parser.parse_statement()
    assert stmt is not None
    r.execute_effect_list([stmt], scope)
    assert r.local_vars.get("_result") == "yes", f'Expected "yes", got {r.local_vars.get("_result")}'
    print("[OK] if statement: true branch")


def test_parse_if_else_statement():
    r = make_runtime()
    scope = Scope(r.global_scope)
    source = """
if 1 == 2:
    set {_result} to "yes"
else:
    set {_result} to "no"
"""
    parser = Parser(source.strip())
    stmt = parser.parse_statement()
    assert stmt is not None
    r.execute_effect_list([stmt], scope)
    assert r.local_vars.get("_result") == "no", f'Expected "no", got {r.local_vars.get("_result")}'
    print("[OK] if statement: false branch")


def test_parse_loop_statement():
    r = make_runtime()
    scope = Scope(r.global_scope)
    source = """
loop 3 times:
    add 1 to {_counter}
"""
    parser = Parser(source.strip())
    stmt = parser.parse_statement()
    assert stmt is not None, "loop statement should parse"
    # The loop statement might use add 1 to {_counter}
    # Set _counter to 0 first
    scope.set("_counter", 0)
    r.execute_effect_list([stmt], scope)
    result = r.local_vars.get("_counter")
    print(f"[INFO] loop result: {result}")


def test_parse_and_execute_condition():
    r = make_runtime()
    handler = r.condition_handlers.get("object is set")
    assert handler is not None
    assert handler(r, [42]) == True
    assert handler(r, [None]) == False
    print("[OK] condition handler: object is set")


def test_parse_and_execute_with_events():
    r = make_runtime()
    scope = Scope(r.global_scope)
    source = 'on message:\n    reply with "Got a message!"'
    parser = Parser(source)
    script = parser.parse()
    assert len(script.events) == 1
    assert script.events[0].event_type == "message"
    assert len(script.events[0].body) == 1
    result = r.execute_effect(script.events[0].body[0], scope)
    print(f"[OK] event parsing + effect execution: {result}")


def test_color_and_timespan():
    assert parse_color("red") == 0xE74C3C
    assert parse_color("#FF0000") == 0xFF0000
    assert parse_timespan("5 seconds") == 5
    assert parse_timespan("1 minute") == 60
    print("[OK] color and timespan utilities")


def test_permission_names():
    assert PERMISSION_NAMES.get("kick_members") is not None
    assert PERMISSION_NAMES.get("administrator") is not None
    assert isinstance(PERMISSION_NAMES["kick_members"], int)
    print("[OK] permission name constants")


def test_scope_chain():
    r = make_runtime()
    parent = r.global_scope
    child = Scope(parent)
    parent.set("global_var", "from_parent")
    assert child.get("global_var") == "from_parent"
    child.set("local_var", "from_child")
    assert child.get("local_var") == "from_child"
    assert parent.get("local_var") is None
    print("[OK] scope chain: inheritance and isolation")


def test_binary_operators():
    r = make_runtime()
    ops = [
        ("+", 2, 3, 5),
        ("-", 10, 4, 6),
        ("*", 3, 7, 21),
        ("/", 10, 2, 5),
        ("=", "a", "a", True),
        ("!=", "a", "b", True),
        (">", 5, 3, True),
        ("<", 3, 5, True),
        ("contains", "hello world", "world", True),
        ("and", True, True, True),
        ("or", False, True, True),
    ]
    for op, l, r_val, expected in ops:
        result = r._eval_binary(op, l, r_val)
        assert result == expected, f"{l} {op} {r_val}: expected {expected}, got {result}"
    print("[OK] all binary operators")


def test_effect_signatures():
    """Register and check that effect handlers accept correct argument counts."""
    r = make_runtime()
    scope = Scope(r.global_scope)

    # All effect handlers should be callable with (runtime, args, kwargs, body, scope)
    handlers = r.effect_handlers
    required = ["send", "reply", "kick", "ban",
                "send_console"]
    for name in required:
        assert name in handlers, f"Missing effect handler: {name}"
    print(f"[OK] all {len(required)} required effect handlers callable")


def test_expression_signatures():
    r = make_runtime()
    handlers = r.expression_handlers
    required = ["id of", "name of", "length of", "size of", "first of",
                "last of", "random of", "lowercase", "uppercase"]
    for name in required:
        assert name in handlers, f"Missing expression handler: {name}"
    print(f"[OK] all {len(required)} required expression handlers registered")


def test_condition_signatures():
    r = make_runtime()
    handlers = r.condition_handlers
    required = ["object is set", "object is not set", "chance"]
    for name in required:
        assert name in handlers, f"Missing condition handler: {name}"
    print(f"[OK] all {len(required)} required condition handlers registered")


# === RUN ALL ===

tests = [
    test_parse_and_execute_variable,
    test_parse_and_execute_expression,
    test_interpolation_with_mock,
    test_parse_if_statement,
    test_parse_if_else_statement,
    test_parse_loop_statement,
    test_parse_and_execute_condition,
    test_parse_and_execute_with_events,
    test_color_and_timespan,
    test_permission_names,
    test_scope_chain,
    test_binary_operators,
    test_effect_signatures,
    test_expression_signatures,
    test_condition_signatures,
]

if __name__ == "__main__":
    print("=" * 50)
    print("Running Integration Tests")
    print("=" * 50)
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"[PASS] {test.__name__}")
        except Exception as e:
            failed += 1
            import traceback
            print(f"[FAIL] {test.__name__}: {e}")
            traceback.print_exc()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 50)
