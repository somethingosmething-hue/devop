"""Test the builtins: effects, expressions, conditions, and sections."""
from language.runtime import Runtime, Scope, StopSignal, ReturnValue, ContinueSignal, BreakSignal
from language.types import TypeRegistry, parse_color, parse_timespan
from language.builtins.effects import register_effects
from language.builtins.expressions import register_expressions
from language.builtins.conditions import register_conditions
from language.builtins.sections import process_section, SectionDefinitions
from language.ast import *
import datetime


def make_runtime():
    runtime = Runtime(TypeRegistry())
    register_effects(runtime)
    register_expressions(runtime)
    register_conditions(runtime)
    return runtime


def test_effect_registration():
    runtime = make_runtime()
    assert len(runtime.effect_handlers) > 50, f"Expected 50+ effects, got {len(runtime.effect_handlers)}"
    print(f"[OK] {len(runtime.effect_handlers)} effect handlers registered")

    required = ["send", "send_console", "reply", "post", "kick", "ban", "timeout",
                "add_role", "remove_role", "make_embed", "make_row", "play_track",
                "defer_interaction", "show_modal", "load_audio", "set_presence",
                "set_volume", "set_repeat", "set_autoplay"]
    for name in required:
        assert name in runtime.effect_handlers, f"Missing effect: {name}"
    print(f"[OK] All required effect handlers present")


def test_expression_registration():
    runtime = make_runtime()
    assert len(runtime.expression_handlers) > 60, f"Expected 60+ expressions, got {len(runtime.expression_handlers)}"
    print(f"[OK] {len(runtime.expression_handlers)} expression handlers registered")

    required = ["id of", "name of", "mention tag of", "length of", "size of",
                "first of", "last of", "random of", "parsed as", "split by",
                "joined by", "lowercase", "uppercase", "trimmed", "subtext",
                "replaced", "hex", "now", "bot", "user", "member", "guild",
                "channel", "role", "emote", "avatar of", "banner of",
                "content of", "topic of", "members of", "roles of",
                "channels of", "emotes of", "owner of", "argument"]
    for name in required:
        assert name in runtime.expression_handlers, f"Missing expression: {name}"
    print(f"[OK] All required expression handlers present")


def test_condition_registration():
    runtime = make_runtime()
    assert len(runtime.condition_handlers) >= 15, f"Expected 15+ conditions, got {len(runtime.condition_handlers)}"
    print(f"[OK] {len(runtime.condition_handlers)} condition handlers registered")

    required = ["object is set", "object is not set", "user is bot",
                "member has role", "member has permission", "message is edited",
                "message is pinned", "channel is nsfw", "thread is archived",
                "thread is locked", "emote is animated", "event is cancelled",
                "chance", "attachment is image", "attachment is audio"]
    for name in required:
        assert name in runtime.condition_handlers, f"Missing condition: {name}"
    print(f"[OK] All required condition handlers present")


def test_scope():
    runtime = make_runtime()
    scope = Scope(runtime.global_scope)

    scope.set("test_var", 42)
    assert scope.get("test_var") == 42
    print(f"[OK] Scope set/get works")

    scope.set("test_var", 100)
    assert scope.get("test_var") == 100
    print(f"[OK] Scope overwrite works")

    assert scope.has("test_var")
    assert not scope.has("nonexistent")
    print(f"[OK] Scope has works")

    scope.delete("test_var")
    assert not scope.has("test_var")
    print(f"[OK] Scope delete works")


def test_runtime_binary_ops():
    runtime = make_runtime()

    assert runtime._eval_binary("+", 1, 2) == 3
    assert runtime._eval_binary("+", "hello", " world") == "hello world"
    assert runtime._eval_binary("-", 10, 3) == 7
    assert runtime._eval_binary("*", 5, 6) == 30
    assert runtime._eval_binary("/", 10, 2) == 5
    assert runtime._eval_binary("=", "a", "a") == True
    assert runtime._eval_binary("!=", "a", "b") == True
    assert runtime._eval_binary(">", 5, 3) == True
    assert runtime._eval_binary("contains", "hello world", "world") == True
    assert runtime._eval_binary("and", True, False) == False
    assert runtime._eval_binary("or", True, False) == True
    print(f"[OK] Binary operators work correctly")


def test_runtime_unary_ops():
    runtime = make_runtime()

    assert runtime._eval_unary("-", 5) == -5
    assert runtime._eval_unary("not", True) == False
    assert runtime._eval_unary("is_set", 42) == True
    assert runtime._eval_unary("is_set", None) == False
    print(f"[OK] Unary operators work correctly")


def test_truthy():
    runtime = make_runtime()
    assert runtime._is_truthy(True) == True
    assert runtime._is_truthy(False) == False
    assert runtime._is_truthy(None) == False
    assert runtime._is_truthy(1) == True
    assert runtime._is_truthy(0) == False
    assert runtime._is_truthy("hello") == True
    assert runtime._is_truthy("") == False
    assert runtime._is_truthy([1, 2]) == True
    assert runtime._is_truthy([]) == False
    print(f"[OK] Truthy evaluation works")


def test_effect_execute_effect():
    runtime = make_runtime()
    scope = Scope(runtime.global_scope)

    effect = EffectStatement(effect_type="wait", arguments=[NumberLiteral(value=5)])
    result = runtime.execute_effect(effect, scope)
    assert isinstance(result, dict) and "_wait" in result
    print(f"[OK] Wait effect works")

    effect = EffectStatement(effect_type="stop")
    result = runtime.execute_effect(effect, scope)
    assert isinstance(result, StopSignal)
    print(f"[OK] Stop effect works")

    effect = EffectStatement(effect_type="log", arguments=[StringLiteral(value="test log")])
    result = runtime.execute_effect(effect, scope)
    print(f"[OK] Log effect works")

    effect = EffectStatement(effect_type="return", arguments=[NumberLiteral(value=99)])
    result = runtime.execute_effect(effect, scope)
    assert isinstance(result, ReturnValue) and result.value == 99
    print(f"[OK] Return effect works")


def test_expression_evaluation():
    runtime = make_runtime()
    scope = Scope(runtime.global_scope)

    result = runtime.evaluate(StringLiteral(value="hello"), scope)
    assert result == "hello"
    print(f"[OK] String literal evaluation works")

    result = runtime.evaluate(NumberLiteral(value=42), scope)
    assert result == 42
    print(f"[OK] Number literal evaluation works")

    result = runtime.evaluate(BooleanLiteral(value=True), scope)
    assert result == True
    print(f"[OK] Boolean literal evaluation works")

    set_stmt = SetVariable(variable=Variable(name="test"), value=NumberLiteral(value=42))
    runtime.execute_effect_list([set_stmt], scope)
    result = runtime.evaluate(Variable(name="test"), scope)
    assert result == 42
    print(f"[OK] Variable set/get works")

    runtime.local_vars["_x"] = "local_val"
    result = runtime.evaluate(Variable(name="_x", is_local=True), scope)
    assert result == "local_val"
    print(f"[OK] Local variable works")

    expr = BinaryOp(left=NumberLiteral(value=10), op="+", right=NumberLiteral(value=20))
    result = runtime.evaluate(expr, scope)
    assert result == 30
    print(f"[OK] Binary expression evaluation works")


def test_expression_handlers():
    runtime = make_runtime()

    handler = runtime.expression_handlers.get("length of")
    assert handler(runtime, ["hello"]) == 5
    print(f"[OK] length of handler works")

    handler = runtime.expression_handlers.get("size of")
    assert handler(runtime, [[1, 2, 3]]) == 3
    print(f"[OK] size of handler works")

    handler = runtime.expression_handlers.get("first of")
    assert handler(runtime, [[1, 2, 3]]) == 1

    handler = runtime.expression_handlers.get("last of")
    assert handler(runtime, [[1, 2, 3]]) == 3
    print(f"[OK] first/last of handlers work")

    handler = runtime.expression_handlers.get("parsed as")
    assert handler(runtime, ["42", "number"]) == 42.0
    assert handler(runtime, ["42", "integer"]) == 42
    assert handler(runtime, ["true", "boolean"]) == True
    print(f"[OK] parsed as handler works")

    handler = runtime.expression_handlers.get("split by")
    assert handler(runtime, ["a,b,c", ","]) == ["a", "b", "c"]

    handler = runtime.expression_handlers.get("joined by")
    assert handler(runtime, [["a", "b", "c"], ","]) == "a,b,c"
    print(f"[OK] split/join handlers work")

    handler = runtime.expression_handlers.get("lowercase")
    assert handler(runtime, ["HELLO"]) == "hello"

    handler = runtime.expression_handlers.get("uppercase")
    assert handler(runtime, ["hello"]) == "HELLO"
    print(f"[OK] case conversion handlers work")

    handler = runtime.expression_handlers.get("hex")
    result = handler(runtime, ["FF0000"])
    assert result == 0xFF0000
    print(f"[OK] hex handler works")

    handler = runtime.expression_handlers.get("round of")
    assert handler(runtime, [3.7]) == 4

    handler = runtime.expression_handlers.get("floor of")
    assert handler(runtime, [3.7]) == 3

    handler = runtime.expression_handlers.get("ceil of")
    assert handler(runtime, [3.2]) == 4

    handler = runtime.expression_handlers.get("absolute of")
    assert handler(runtime, [-5]) == 5

    handler = runtime.expression_handlers.get("sqrt of")
    assert handler(runtime, [9]) == 3.0
    print(f"[OK] math expression handlers work")


def test_condition_handlers():
    runtime = make_runtime()

    handler = runtime.condition_handlers["object is set"]
    assert handler(runtime, [42]) == True
    assert handler(runtime, [None]) == False

    handler = runtime.condition_handlers["object is not set"]
    assert handler(runtime, [None]) == True
    assert handler(runtime, [42]) == False
    print(f"[OK] is set/not set conditions work")

    handler = runtime.condition_handlers["chance"]
    assert isinstance(handler(runtime, [100]), bool)
    print(f"[OK] chance condition works")


def test_type_system():
    registry = TypeRegistry()

    assert registry.get("text") is not None
    assert registry.get("user") is not None
    assert registry.get("member") is not None
    assert registry.get("guild") is not None
    assert registry.get("message") is not None
    assert registry.get("channel") is not None
    assert registry.get("role") is not None
    print(f"[OK] Type registry has all core types")

    prop_type = registry.resolve_property("member", "avatar")
    assert prop_type == "text", f"Expected 'text', got '{prop_type}'"
    print(f"[OK] Inherited property resolution works")

    prop_type = registry.resolve_property("member", "nickname")
    assert prop_type == "text", f"Expected 'text', got '{prop_type}'"
    print(f"[OK] Own property resolution works")

    assert registry.can_assign("member", "user") == True
    assert registry.can_assign("textchannel", "channel") == True
    assert registry.can_assign("textchannel", "voicechannel") == False
    print(f"[OK] Type coercion works")

    assert parse_color("blue") == 0x3498DB
    assert parse_color("#FF0000") == 0xFF0000
    assert parse_color("red") == 0xE74C3C
    print(f"[OK] Color parsing works")

    assert parse_timespan("5 seconds") == 5
    assert parse_timespan("1 minute") == 60
    assert parse_timespan("2 hours") == 7200
    assert parse_timespan("1 day") == 86400
    print(f"[OK] Timespan parsing works")


def test_builtin_expressions():
    runtime = make_runtime()

    class MockObj:
        def __init__(self):
            self.id = 12345
            self.name = "TestObject"

    obj = MockObj()

    id_fn = runtime.expression_handlers.get("id of")
    assert id_fn(runtime, [obj]) == "12345"
    print(f"[OK] id of expression works with mock object")

    name_fn = runtime.expression_handlers.get("name of")
    assert name_fn(runtime, [obj]) == "TestObject"
    print(f"[OK] name of expression works with mock object")

    sum_fn = runtime.expression_handlers.get("sum of")
    assert sum_fn(runtime, [[1, 2, 3]]) == 6.0
    print(f"[OK] sum of expression works")

    avg_fn = runtime.expression_handlers.get("average of")
    assert avg_fn(runtime, [[1, 2, 3]]) == 2.0
    print(f"[OK] average of expression works")

    max_fn = runtime.expression_handlers.get("max of")
    assert max_fn(runtime, [[1, 5, 3]]) == 5
    print(f"[OK] max of expression works")

    min_fn = runtime.expression_handlers.get("min of")
    assert min_fn(runtime, [[1, 5, 3]]) == 1
    print(f"[OK] min of expression works")

    index_fn = runtime.expression_handlers.get("index of")
    assert index_fn(runtime, ["b", ["a", "b", "c"]]) == 1
    print(f"[OK] index of expression works")

    trim_fn = runtime.expression_handlers.get("trimmed")
    assert trim_fn(runtime, ["  hello  "]) == "hello"
    print(f"[OK] trimmed expression works")

    replaced_fn = runtime.expression_handlers.get("replaced")
    assert replaced_fn(runtime, ["hello world", "world", "there"]) == "hello there"
    print(f"[OK] replaced expression works")

    permission_fn = runtime.expression_handlers.get("permission")
    assert permission_fn(runtime, ["kick_members"]) > 0
    print(f"[OK] permission expression works")


def test_effect_send_console():
    runtime = make_runtime()
    scope = Scope(runtime.global_scope)

    result = runtime.effect_handlers["send_console"](
        runtime, [StringLiteral(value="Hello console!")], {}, [], scope
    )
    assert result == "Hello console!"
    print(f"[OK] send to console effect works")


def test_sections():
    runtime = make_runtime()
    scope = Scope(runtime.global_scope)

    embed_section = process_section(runtime, "embed", [], scope)
    assert embed_section is not None
    print(f"[OK] embed section processor works")

    row_section = process_section(runtime, "component_row", [], scope)
    assert row_section is not None
    assert row_section.get("type") == "component_row"
    print(f"[OK] component row section processor works")

    defs = SectionDefinitions.get_section("embed")
    assert "description" in defs
    assert "children" in defs
    assert "handler" in defs
    print(f"[OK] section definitions work")


def test_parse_reply():
    from language.parser import Parser

    source = 'reply with "Hello!"'
    parser = Parser(source)
    stmt = parser.parse_statement()
    assert stmt is not None
    assert stmt.effect_type == "reply"
    assert stmt.keyword_args.get("hidden") == False
    print(f"[OK] reply with (visible) is parsed correctly")

    source = 'reply with hidden "Secret!"'
    parser = Parser(source)
    stmt = parser.parse_statement()
    assert stmt is not None
    assert stmt.effect_type == "reply"
    assert stmt.keyword_args.get("hidden") == True
    print(f"[OK] reply with hidden (ephemeral) is parsed correctly")


if __name__ == "__main__":
    print("=" * 50)
    print("Running Builtins Tests")
    print("=" * 50)

    tests = [
        test_parse_reply,
        test_effect_registration,
        test_expression_registration,
        test_condition_registration,
        test_scope,
        test_runtime_binary_ops,
        test_runtime_unary_ops,
        test_truthy,
        test_effect_execute_effect,
        test_expression_evaluation,
        test_expression_handlers,
        test_condition_handlers,
        test_type_system,
        test_builtin_expressions,
        test_effect_send_console,
        test_sections,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 50)
