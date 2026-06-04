from __future__ import annotations
from .ast import *
from .types import TypeRegistry, parse_color, parse_timespan, format_timespan, PERMISSION_NAMES
from .parser import IdentifierRef
from typing import Any, Optional, Callable
import datetime
import math
import random
import re
import traceback


class RuntimeError_(Exception):
    def __init__(self, message: str, node: ASTNode | None = None):
        self.node = node
        loc = f"Line {node.line}:{node.column}" if node else "unknown"
        super().__init__(f"[ERROR] {loc}: {message}")


class Scope:
    def __init__(self, parent: Optional[Scope] = None, is_async_safe: bool = False):
        self.variables: dict[str, Any] = {}
        self.parent = parent
        self.is_async_safe = is_async_safe

    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, value: Any) -> None:
        if name in self.variables or self.parent is None:
            self.variables[name] = value
        elif self.parent:
            if self.parent.has(name):
                self.parent.set(name, value)
            else:
                self.variables[name] = value

    def has(self, name: str) -> bool:
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

    def delete(self, name: str) -> bool:
        if name in self.variables:
            del self.variables[name]
            return True
        if self.parent:
            return self.parent.delete(name)
        return False

    def clear(self) -> None:
        self.variables.clear()


class EventContext:
    def __init__(self):
        self.values: dict[str, Any] = {}
        self.cancelled = False
        self.bot_name: str = ""
        self.interaction: Any = None

    def get(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)

    def set(self, name: str, value: Any) -> None:
        self.values[name] = value


class Runtime:
    def __init__(self, type_registry: TypeRegistry | None = None):
        self.types = type_registry or TypeRegistry()
        self.global_scope = Scope()
        self.functions: dict[str, FunctionDecl] = {}
        self.event_handlers: list[EventHandler] = []
        self.registered_commands: list[CommandDecl] = []
        self.slash_commands: list[SlashCommandDecl] = []
        self.embed_templates: dict[str, EmbedBuilder] = {}
        self.event_context: EventContext = EventContext()
        self.local_vars: dict[str, Any] = {}
        self.option_vars: dict[str, Any] = {}
        self.current_bot: Any = None
        self.bot_instances: dict[str, Any] = {}
        self.audio_queues: dict[str, list] = {}
        self.connected_voice: dict[str, Any] = {}
        self.effect_handlers: dict[str, Callable] = {}
        self.condition_handlers: dict[str, Callable] = {}
        self.expression_handlers: dict[str, Callable] = {}
        self.custom_event_handlers: dict[str, list[EventHandler]] = {}
        self.bot_manager: Any = None

    def set_bot_manager(self, mgr: Any) -> None:
        self.bot_manager = mgr

    def evaluate(self, node: Any, scope: Scope | None = None) -> Any:
        if node is None:
            return None
        if scope is None:
            scope = self.global_scope

        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, StringLiteral):
            val = node.value
            if val and "%" in val:
                return self._interpolate_string(val, scope)
            return val
        if isinstance(node, BooleanLiteral):
            return node.value
        if isinstance(node, NullLiteral):
            return None

        if isinstance(node, Variable):
            if node.is_local:
                raw = self.local_vars.get(node.name)
                if raw is not None:
                    return raw
                if "::*" in node.name:
                    base_name = node.name.replace("::*", "")
                    raw = self.local_vars.get(base_name)
                    if isinstance(raw, dict):
                        return list(raw.values())
                    if isinstance(raw, list):
                        return raw
                    return []
                return None
            if node.is_option:
                return self.option_vars.get(node.name)
            if "::*" in node.name:
                base_name = node.name.replace("::*", "")
                raw = scope.get(base_name)
                if raw is None:
                    raw = self.global_scope.get(base_name)
                if isinstance(raw, dict):
                    return list(raw.values())
                if isinstance(raw, list):
                    return raw
                return []
            val = scope.get(node.name)
            if val is None:
                val = self.global_scope.get(node.name)
            return val

        if isinstance(node, ListAccess):
            var = self.evaluate(node.variable, scope)
            idx = self.evaluate(node.index, scope)
            if isinstance(var, dict):
                return var.get(str(idx))
            if isinstance(var, list):
                if isinstance(idx, int) and 0 <= idx < len(var):
                    return var[idx]
                return None
            return None

        if isinstance(node, PropertyAccess):
            obj = self.evaluate(node.obj, scope)
            prop = node.property_name
            return self._resolve_property(obj, prop)

        if isinstance(node, BinaryOp):
            left = self.evaluate(node.left, scope)
            right = self.evaluate(node.right, scope) if node.right else None
            return self._eval_binary(node.op, left, right, node)

        if isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand, scope)
            return self._eval_unary(node.op, operand, node)

        if isinstance(node, FunctionCall):
            return self._call_function(node, scope)

        if isinstance(node, InlineConditional):
            cond = self.evaluate(node.condition, scope)
            if self._is_truthy(cond):
                return self.evaluate(node.true_value, scope)
            return self.evaluate(node.false_value, scope)

        if isinstance(node, NewBuilder):
            return self._build_new_object(node, scope)

        if isinstance(node, IdentifierRef):
            return self._resolve_identifier(node.name, scope)

        if isinstance(node, EffectStatement):
            return self.execute_effect(node, scope)

        if isinstance(node, list):
            results = []
            for item in node:
                results.append(self.evaluate(item, scope))
            return results

        return node

    def _call_function(self, node: FunctionCall, scope: Scope) -> Any:
        name = node.name
        if name in self.functions:
            fn = self.functions[name]
            fn_scope = Scope(self.global_scope)
            for i, (pname, ptype, default) in enumerate(fn.parameters):
                if i < len(node.arguments):
                    val = self.evaluate(node.arguments[i], scope)
                elif default is not None:
                    val = self.evaluate(default, scope)
                else:
                    val = None
                fn_scope.set(pname, val)
            result = self.execute_effect_list(fn.body, fn_scope)
            if isinstance(result, ReturnValue):
                return result.value
            return result
        if name in self.expression_handlers:
            args = [self.evaluate(a, scope) for a in node.arguments]
            return self.expression_handlers[name](self, args)
        if name in self.effect_handlers:
            args = [self.evaluate(a, scope) for a in node.arguments]
            return self.effect_handlers[name](self, args, {}, None, scope)
        return None

    def _resolve_property(self, obj: Any, prop: str) -> Any:
        if obj is None:
            return None
        if hasattr(obj, prop):
            attr = getattr(obj, prop)
            return attr() if callable(attr) else attr
        if hasattr(obj, prop.replace("_", "")):
            attr = getattr(obj, prop.replace("_", ""))
            return attr() if callable(attr) else attr
        if isinstance(obj, dict):
            return obj.get(prop)
        if isinstance(obj, list):
            if prop == "size":
                return len(obj)
            if prop == "first" and obj:
                return obj[0]
            if prop == "last" and obj:
                return obj[-1]
            if prop == "random" and obj:
                return random.choice(obj)
        if isinstance(obj, str):
            if prop == "length":
                return len(obj)
            if prop == "lowercase":
                return obj.lower()
            if prop == "uppercase":
                return obj.upper()
        return None

    def _interpolate_string(self, value: str, scope: Scope) -> str:
        parts = []
        last = 0
        for m in re.finditer(r'%([^%]+)%', value):
            parts.append(value[last:m.start()])
            expr_text = m.group(1).strip()
            try:
                from language.parser import Parser
                parser = Parser(expr_text)
                expr = parser.parse_expression()
                result = self.evaluate(expr, scope)
                parts.append(str(result) if result is not None else "")
            except Exception:
                parts.append(m.group(0))
            last = m.end()
        parts.append(value[last:])
        return "".join(parts)

    def _eval_binary(self, op: str, left: Any, right: Any, node: ASTNode | None = None) -> Any:
        if op == "+":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            return str(left or "") + str(right or "")
        if op == "-":
            return (left or 0) - (right or 0)
        if op == "*":
            return (left or 0) * (right or 0)
        if op == "/":
            if right == 0:
                raise RuntimeError_("Division by zero", node)
            return (left or 0) / (right or 0)
        if op == "^":
            return (left or 0) ** (right or 0)
        if op == "=":
            return str(left) == str(right)
        if op == "!=":
            return str(left) != str(right)
        if op == ">":
            return (left or 0) > (right or 0)
        if op == ">=":
            return (left or 0) >= (right or 0)
        if op == "<":
            return (left or 0) < (right or 0)
        if op == "<=":
            return (left or 0) <= (right or 0)
        if op == "and":
            return self._is_truthy(left) and self._is_truthy(right)
        if op == "or":
            return self._is_truthy(left) or self._is_truthy(right)
        if op == "contains":
            return str(right or "") in str(left or "")
        if op == "starts_with":
            return str(left or "").startswith(str(right or ""))
        if op == "ends_with":
            return str(left or "").endswith(str(right or ""))
        if op == "matches":
            try:
                return bool(re.match(str(right or ""), str(left or "")))
            except re.error:
                return False
        return None

    def _eval_unary(self, op: str, operand: Any, node: ASTNode | None = None) -> Any:
        if op == "-":
            return -(operand or 0)
        if op == "not":
            return not self._is_truthy(operand)
        if op == "is_set":
            return operand is not None
        return None

    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0 and value.lower() not in ("false", "0", "no")
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True

    def _resolve_identifier(self, name: str, scope: Scope) -> Any:
        if name.startswith("@"):
            return self.option_vars.get(name[1:])
        named_refs = {
            "now": datetime.datetime.now(),
            "true": True, "false": False, "null": None,
            "event": self.event_context,
            "event-bot": self.event_context.get("bot"),
            "event-message": self.event_context.get("message"),
            "event-channel": self.event_context.get("channel"),
            "event-author": self.event_context.get("author"),
            "event-user": self.event_context.get("user"),
            "event-member": self.event_context.get("member"),
            "event-guild": self.event_context.get("guild"),
            "event-emote": self.event_context.get("emote"),
            "event-string": self.event_context.get("string"),
            "event-boolean": self.event_context.get("boolean"),
            "event-dropdown": self.event_context.get("dropdown"),
            "event-timespan": self.event_context.get("timespan"),
            "event-role": self.event_context.get("role"),
            "selected values": self.event_context.get("selected_values"),
            "selected entities": self.event_context.get("selected_entities"),
            "current argument": self.event_context.get("current_argument"),
            "target message": self.event_context.get("target_message"),
            "target user": self.event_context.get("target_user"),
            "used command": self.event_context.get("command_name"),
            "used prefix": self.event_context.get("prefix"),
            "last exception": self.event_context.get("last_exception"),
        }
        if name in named_refs:
            return named_refs[name]
        if name.startswith("event-") or name.startswith("event_"):
            key = name[6:] if name.startswith("event-") else name[6:]
            val = self.event_context.get(key)
            if val is not None:
                return val
        if name in self.event_context.values:
            return self.event_context.values[name]
        val = scope.get(name)
        if val is not None:
            return val
        val = self.global_scope.get(name)
        if val is not None:
            return val
        return None

    def execute_effect(self, effect: EffectStatement, scope: Scope) -> Any:
        etype = effect.effect_type
        args = effect.arguments
        kwargs = effect.keyword_args
        body = effect.body

        if etype in self.effect_handlers:
            return self.effect_handlers[etype](self, args, kwargs, body, scope)

        if etype == "set":
            var = self.evaluate(args[0], scope) if isinstance(args[0], Expression) else args[0]
            val = self.evaluate(args[1], scope) if len(args) > 1 else None
            if isinstance(var, str):
                if var.startswith("_"):
                    self.local_vars[var] = val
                else:
                    scope.set(var, val)
                    self.global_scope.set(var, val)
            return val

        if etype == "add":
            val = self.evaluate(args[0], scope) if len(args) > 0 else None
            var_expr = args[1] if len(args) > 1 else None
            if var_expr:
                var = self.evaluate(var_expr, scope) if isinstance(var_expr, Expression) else var_expr
            else:
                var = None
            if isinstance(var, str):
                current = scope.get(var) or self.global_scope.get(var) or 0
                if isinstance(current, (int, float)):
                    current += (val or 0)
                elif isinstance(current, list):
                    current.append(val)
                elif isinstance(current, dict):
                    current[str(val)] = val
                else:
                    current = (current or 0) + (val or 0)
                scope.set(var, current)
                self.global_scope.set(var, current)
            return val

        if etype == "remove":
            val = self.evaluate(args[0], scope) if len(args) > 0 else None
            var_expr = args[1] if len(args) > 1 else None
            var = self.evaluate(var_expr, scope) if isinstance(var_expr, Expression) else var_expr
            if isinstance(var, str):
                current = scope.get(var) or self.global_scope.get(var) or 0
                if isinstance(current, (int, float)):
                    current -= (val or 0)
                elif isinstance(current, list) and val in current:
                    current.remove(val)
                elif isinstance(current, dict) and val in current:
                    del current[str(val)]
                scope.set(var, current)
                self.global_scope.set(var, current)
            return val

        if etype == "delete":
            var_expr = args[0] if args else None
            if var_expr:
                name = self.evaluate(var_expr, scope) if isinstance(var_expr, Expression) else var_expr
                if isinstance(name, str):
                    scope.delete(name)
                    self.global_scope.delete(name)
            return None

        if etype == "clear":
            var_expr = args[0] if args else None
            if var_expr:
                name = self.evaluate(var_expr, scope) if isinstance(var_expr, Expression) else var_expr
                if isinstance(name, str):
                    scope.set(name, [])
                    self.global_scope.set(name, [])
            return None

        if etype == "wait":
            dur = self.evaluate(args[0], scope) if args else None
            return {"_wait": dur}

        if etype == "stop" or etype == "stop_trigger":
            return StopSignal()

        if etype == "cancel_event":
            self.event_context.cancelled = True
            return None

        if etype == "uncancel_event":
            self.event_context.cancelled = False
            return None

        if etype == "return":
            val = self.evaluate(args[0], scope) if args else None
            return ReturnValue(val)

        if etype == "throw":
            msg = self.evaluate(args[0], scope) if args else "Unknown error"
            raise RuntimeError_(str(msg), effect)

        if etype == "log":
            val = self.evaluate(args[0], scope) if args else ""
            print(f"[LOG] {val}")
            return val

        if etype == "call_function":
            fn_call = args[0]
            if isinstance(fn_call, FunctionCall):
                return self._call_function(fn_call, scope)
            return None

        if etype == "continue":
            return ContinueSignal()

        return None

    def _build_new_object(self, node: NewBuilder, scope: Scope) -> Any:
        if node.type_name == "embed":
            import discord
            embed = discord.Embed()
            for key, val in node.properties.items():
                resolved = self.evaluate(val, scope)
                if key == "title":
                    embed.title = str(resolved) if resolved else None
                elif key == "description":
                    embed.description = str(resolved) if resolved else None
                elif key == "color":
                    embed.color = parse_color(resolved)
                elif key == "field":
                    pass
                elif key == "footer":
                    if isinstance(resolved, dict):
                        embed.set_footer(**resolved)
                    elif resolved:
                        embed.set_footer(text=str(resolved))
            return embed
        if node.type_name == "message":
            return {"type": "message", "content": self.evaluate(node.properties.get("content"), scope),
                    "embed": self.evaluate(node.properties.get("embed"), scope),
                    "components": self.evaluate(node.properties.get("components"), scope)}
        if node.type_name == "button":
            style_map = {"primary": 1, "secondary": 2, "success": 3, "danger": 4, "link": 5}
            return {
                "type": "button", "style": style_map.get(str(self.evaluate(node.properties.get("style"), scope)), 1),
                "id": str(self.evaluate(node.properties.get("id"), scope) or ""),
                "label": str(self.evaluate(node.properties.get("label"), scope) or ""),
                "emoji": self.evaluate(node.properties.get("emoji"), scope),
            }
        if node.type_name == "dropdown":
            return {"type": "dropdown", "id": str(self.evaluate(node.properties.get("id"), scope) or "")}
        if node.type_name == "entity_dropdown":
            return {"type": "entity_dropdown", "id": str(self.evaluate(node.properties.get("id"), scope) or "")}
        if node.type_name == "modal":
            return {"type": "modal", "title": str(self.evaluate(node.properties.get("title"), scope) or ""),
                    "id": str(self.evaluate(node.properties.get("id"), scope) or "")}
        if node.type_name == "text_input":
            return {"type": "text_input", "id": str(self.evaluate(node.properties.get("id"), scope) or "")}
        if node.type_name == "label":
            return {"type": "label", "text": str(self.evaluate(node.properties.get("text"), scope) or "")}
        if node.type_name == "slash_command":
            return {"type": "slash_command", "name": str(self.evaluate(node.properties.get("name"), scope) or "")}
        if node.type_name == "container":
            return {"type": "container", "id": self.evaluate(node.properties.get("id"), scope)}
        if node.type_name == "component_row":
            return {"type": "component_row", "components": self.evaluate(node.properties.get("components"), scope) or []}
        return node.properties

    def execute_effect_list(self, effects: list[Statement], scope: Scope) -> Any:
        for stmt in effects:
            try:
                if isinstance(stmt, SetVariable):
                    var_name = stmt.variable.name if isinstance(stmt.variable, Variable) else self.evaluate(stmt.variable, scope)
                    if not isinstance(var_name, str):
                        var_name = str(var_name) if var_name is not None else None
                    val = self.evaluate(stmt.value, scope)
                    if var_name:
                        if var_name.startswith("_"):
                            self.local_vars[var_name] = val
                        else:
                            scope.set(var_name, val)
                            self.global_scope.set(var_name, val)
                    continue
                if isinstance(stmt, AddToVariable):
                    val = self.evaluate(stmt.value, scope)
                    var_expr = stmt.variable
                    var = var_expr.name if isinstance(var_expr, Variable) else (self.evaluate(var_expr, scope) if isinstance(var_expr, Expression) else var_expr)
                    if not isinstance(var, str):
                        var = str(var) if var is not None else None
                    if var:
                        current = scope.get(var) or self.global_scope.get(var) or 0
                        if isinstance(current, (int, float)):
                            current += (val or 0)
                        elif isinstance(current, list):
                            current.append(val)
                        elif isinstance(current, dict):
                            current[str(val)] = val
                        else:
                            current = (current or 0) + (val or 0)
                        scope.set(var, current)
                        self.global_scope.set(var, current)
                    continue
                if isinstance(stmt, RemoveFromVariable):
                    val = self.evaluate(stmt.value, scope)
                    var_expr = stmt.variable
                    var = var_expr.name if isinstance(var_expr, Variable) else (self.evaluate(var_expr, scope) if isinstance(var_expr, Expression) else var_expr)
                    if not isinstance(var, str):
                        var = str(var) if var is not None else None
                    if var:
                        current = scope.get(var) or self.global_scope.get(var) or 0
                        if isinstance(current, (int, float)):
                            current -= (val or 0)
                        elif isinstance(current, list) and val in current:
                            current.remove(val)
                        elif isinstance(current, dict) and str(val) in current:
                            del current[str(val)]
                        scope.set(var, current)
                        self.global_scope.set(var, current)
                    continue
                if isinstance(stmt, DeleteVariable):
                    var = stmt.variable.name if isinstance(stmt.variable, Variable) else (self.evaluate(stmt.variable, scope) if isinstance(stmt.variable, Expression) else stmt.variable)
                    if not isinstance(var, str):
                        var = str(var) if var is not None else None
                    if var:
                        scope.delete(var)
                        self.global_scope.delete(var)
                    continue
                if isinstance(stmt, ClearVariable):
                    var = stmt.variable.name if isinstance(stmt.variable, Variable) else (self.evaluate(stmt.variable, scope) if isinstance(stmt.variable, Expression) else stmt.variable)
                    if not isinstance(var, str):
                        var = str(var) if var is not None else None
                    if var:
                        scope.set(var, [])
                        self.global_scope.set(var, [])
                    continue

                if isinstance(stmt, IfStatement):
                    cond = self.evaluate(stmt.condition, scope)
                    if self._is_truthy(cond):
                        result = self.execute_effect_list(stmt.body, scope)
                    else:
                        matched = False
                        for econd, ebody in stmt.elif_conditions:
                            if self._is_truthy(self.evaluate(econd, scope)):
                                result = self.execute_effect_list(ebody, scope)
                                matched = True
                                break
                        if not matched:
                            result = self.execute_effect_list(stmt.else_body, scope)
                    if isinstance(result, (StopSignal, ReturnValue)):
                        return result
                    continue

                if isinstance(stmt, LoopStatement):
                    result = self._execute_loop(stmt, scope)
                    if isinstance(result, (StopSignal, ReturnValue)):
                        return result
                    continue

                if isinstance(stmt, WhileStatement):
                    while self._is_truthy(self.evaluate(stmt.condition, scope)):
                        result = self.execute_effect_list(stmt.body, scope)
                        if isinstance(result, (StopSignal, ReturnValue)):
                            return result
                    continue

                if isinstance(stmt, DoWhileStatement):
                    while True:
                        result = self.execute_effect_list(stmt.body, scope)
                        if isinstance(result, (StopSignal, ReturnValue)):
                            return result
                        if not self._is_truthy(self.evaluate(stmt.condition, scope)):
                            break
                    continue

                if isinstance(stmt, WaitStatement):
                    dur = self.evaluate(stmt.duration, scope)
                    return {"_wait": dur}

                if isinstance(stmt, ReturnStatement):
                    val = self.evaluate(stmt.value, scope)
                    return ReturnValue(val)

                if isinstance(stmt, CancelEventStatement):
                    self.event_context.cancelled = True
                    continue

                if isinstance(stmt, UncancelEventStatement):
                    self.event_context.cancelled = False
                    continue

                if isinstance(stmt, StopTriggerStatement):
                    return StopSignal()

                if isinstance(stmt, ContinueStatement):
                    return ContinueSignal()

                if isinstance(stmt, BreakStatement):
                    return BreakSignal(count=stmt.count)

                if isinstance(stmt, ThrowStatement):
                    msg = self.evaluate(stmt.message, scope)
                    raise RuntimeError_(str(msg), stmt)

                if isinstance(stmt, EffectStatement):
                    result = self.execute_effect(stmt, scope)
                    if isinstance(result, (StopSignal, ReturnValue, ContinueSignal, BreakSignal)):
                        return result
                    if isinstance(result, dict) and "_wait" in result:
                        return result
                    continue

                if isinstance(stmt, Expression):
                    self.evaluate(stmt, scope)
                    continue

            except RuntimeError_:
                raise
            except Exception as e:
                loc = f"Line {stmt.line}:{stmt.column}" if hasattr(stmt, 'line') else "unknown"
                raise RuntimeError_(f"{type(e).__name__}: {e}", stmt)
        return None

    def _execute_loop(self, stmt: LoopStatement, scope: Scope) -> Any:
        if stmt.loop_type == "times":
            count = stmt.max_iterations
            for i in range(count):
                self.local_vars["loop-index"] = i
                self.local_vars["loop-counter"] = i + 1
                self.local_vars["loop-number"] = i + 1
                result = self.execute_effect_list(stmt.body, scope)
                if isinstance(result, BreakSignal):
                    break
                if isinstance(result, ContinueSignal):
                    continue
                if isinstance(result, (StopSignal, ReturnValue)):
                    return result
            return None

        iterable = self.evaluate(stmt.iterable, scope) if stmt.iterable else []
        if iterable is None:
            iterable = []
        if not isinstance(iterable, (list, dict)):
            iterable = [iterable]

        items = list(iterable.values()) if isinstance(iterable, dict) else list(iterable)
        for i, item in enumerate(items):
            self.local_vars["loop-value"] = item
            self.local_vars["loop-index"] = i
            self.local_vars["loop-counter"] = i + 1
            result = self.execute_effect_list(stmt.body, scope)
            if isinstance(result, BreakSignal):
                break
            if isinstance(result, ContinueSignal):
                continue
            if isinstance(result, (StopSignal, ReturnValue)):
                return result
        return None

    def _expand_wildcard(self, var: Any, scope: Scope) -> list:
        if isinstance(var, Variable) and "::*" in var.name:
            base_name = var.name.replace("::*", "")
            val = scope.get(base_name)
            if val is None:
                val = self.global_scope.get(base_name)
            if isinstance(val, dict):
                return list(val.values())
            if isinstance(val, list):
                return val
            return []
        return None

    def _handle_embed_builder(self, args: list, kwargs: dict, body: list, scope: Scope) -> Any:
        import discord
        embed = discord.Embed()
        template_name = kwargs.get("template")
        if template_name and template_name in self.embed_templates:
            pass
        for stmt in body:
            if isinstance(stmt, EffectStatement):
                if stmt.effect_type.startswith("embed_set_"):
                    prop = stmt.effect_type[10:]
                    val = self.evaluate(stmt.arguments[0], scope) if stmt.arguments else None
                    if prop == "title":
                        embed.title = str(val) if val else None
                    elif prop == "description":
                        embed.description = str(val) if val else None
                    elif prop == "color":
                        embed.color = parse_color(val)
                    elif prop == "author":
                        embed.set_author(name=str(val) if val else "")
                    elif prop == "author_icon":
                        if embed.author:
                            embed.set_author(name=embed.author.name or "", icon_url=str(val) if val else "")
                    elif prop == "author_url":
                        if embed.author:
                            embed.set_author(name=embed.author.name or "", url=str(val) if val else "")
                    elif prop == "image":
                        embed.set_image(url=str(val) if val else "")
                    elif prop == "thumbnail":
                        embed.set_thumbnail(url=str(val) if val else "")
                    elif prop == "footer":
                        embed.set_footer(text=str(val) if val else "")
                    elif prop == "footer_icon":
                        if embed.footer:
                            embed.set_footer(text=embed.footer.text or "", icon_url=str(val) if val else "")
                    elif prop == "title_url":
                        pass
                    elif prop == "timestamp":
                        try:
                            embed.timestamp = val if isinstance(val, datetime.datetime) else datetime.datetime.fromisoformat(str(val))
                        except (ValueError, TypeError):
                            embed.timestamp = datetime.datetime.now()
                elif stmt.effect_type == "embed_add_field":
                    name = str(self.evaluate(stmt.arguments[0], scope) or "")
                    value = str(self.evaluate(stmt.arguments[1], scope) or "")
                    inline = bool(stmt.arguments[2]) if len(stmt.arguments) > 2 else False
                    embed.add_field(name=name, value=value, inline=inline)
        store_in = kwargs.get("store_in")
        if store_in:
            if isinstance(store_in, str):
                if store_in.startswith("_"):
                    self.local_vars[store_in] = embed
                else:
                    scope.set(store_in, embed)
                    self.global_scope.set(store_in, embed)
        return embed


class StopSignal:
    pass


class ReturnValue:
    def __init__(self, value: Any = None):
        self.value = value


class ContinueSignal:
    pass


class BreakSignal:
    def __init__(self, count: int = 1):
        self.count = count
