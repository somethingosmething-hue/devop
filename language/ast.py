from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0

    def set_pos(self, line: int, col: int) -> ASTNode:
        self.line = line
        self.column = col
        return self


@dataclass
class Script(ASTNode):
    options: dict[str, Any] = field(default_factory=dict)
    variables: list[tuple[str, Any]] = field(default_factory=list)
    functions: dict[str, FunctionDecl] = field(default_factory=dict)
    commands: list[CommandDecl] = field(default_factory=list)
    slash_commands: list[SlashCommandDecl] = field(default_factory=list)
    events: list[EventHandler] = field(default_factory=list)
    bot_definitions: list[BotDefinition] = field(default_factory=list)
    global_statements: list[ASTNode] = field(default_factory=list)


# --- Expressions ---
@dataclass
class Expression(ASTNode):
    pass


@dataclass
class Literal(Expression):
    value: Any = None


@dataclass
class NumberLiteral(Literal):
    pass


@dataclass
class StringLiteral(Literal):
    pass


@dataclass
class BooleanLiteral(Literal):
    pass


@dataclass
class NullLiteral(Literal):
    pass


@dataclass
class Variable(Expression):
    name: str = ""
    is_local: bool = False
    is_option: bool = False


@dataclass
class ListAccess(Expression):
    variable: Expression | None = None
    index: Expression | None = None


@dataclass
class PropertyAccess(Expression):
    obj: Expression | None = None
    property_name: str = ""


@dataclass
class BinaryOp(Expression):
    left: Expression | None = None
    op: str = ""
    right: Expression | None = None


@dataclass
class UnaryOp(Expression):
    op: str = ""
    operand: Expression | None = None


@dataclass
class FunctionCall(Expression):
    name: str = ""
    arguments: list[Expression] = field(default_factory=list)


@dataclass
class TypeAnnotation(Expression):
    type_name: str = ""
    nullable: bool = False
    is_lvalue: bool = False


@dataclass
class Placeholder(Expression):
    """%type% placeholder in pattern matching"""
    type_name: str = ""
    optional: bool = False
    target_variable: str = ""
    lvalue: bool = False


@dataclass
class InlineConditional(Expression):
    condition: Expression | None = None
    true_value: Expression | None = None
    false_value: Expression | None = None


@dataclass
class NewBuilder(Expression):
    """set {_x} to new [type]: ..."""
    type_name: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    children: list[tuple] = field(default_factory=list)


# --- Statements / Effects ---
@dataclass
class Statement(ASTNode):
    pass


@dataclass
class EffectStatement(Statement):
    effect_type: str = ""
    arguments: list[Any] = field(default_factory=list)
    keyword_args: dict[str, Any] = field(default_factory=dict)
    body: list[Statement] | None = None


@dataclass
class SetVariable(Statement):
    variable: Expression | None = None
    value: Expression | None = None


@dataclass
class AddToVariable(Statement):
    variable: Expression | None = None
    value: Expression | None = None


@dataclass
class RemoveFromVariable(Statement):
    variable: Expression | None = None
    value: Expression | None = None


@dataclass
class DeleteVariable(Statement):
    variable: Expression | None = None


@dataclass
class ClearVariable(Statement):
    variable: Expression | None = None


# --- Control Flow ---
@dataclass
class IfStatement(Statement):
    condition: Expression | None = None
    body: list[Statement] = field(default_factory=list)
    else_body: list[Statement] = field(default_factory=list)
    elif_conditions: list[tuple[Expression, list[Statement]]] = field(default_factory=list)


@dataclass
class LoopStatement(Statement):
    loop_type: str = ""  # for, while, times, members, guilds, channels, roles
    variable: Expression | None = None
    iterable: Expression | None = None
    body: list[Statement] = field(default_factory=list)
    max_iterations: int = 0


@dataclass
class WhileStatement(Statement):
    condition: Expression | None = None
    body: list[Statement] = field(default_factory=list)


@dataclass
class DoWhileStatement(Statement):
    condition: Expression | None = None
    body: list[Statement] = field(default_factory=list)


@dataclass
class ContinueStatement(Statement):
    pass


@dataclass
class BreakStatement(Statement):
    count: int = 1


@dataclass
class ReturnStatement(Statement):
    value: Expression | None = None


@dataclass
class WaitStatement(Statement):
    duration: Expression | None = None


@dataclass
class CancelEventStatement(Statement):
    pass


@dataclass
class UncancelEventStatement(Statement):
    pass


@dataclass
class StopTriggerStatement(Statement):
    pass


@dataclass
class ThrowStatement(Statement):
    message: Expression | None = None


# --- Function ---
@dataclass
class FunctionDecl(ASTNode):
    name: str = ""
    local: bool = False
    parameters: list[tuple[str, str, Expression | None]] = field(default_factory=list)
    return_type: str = ""
    body: list[Statement] = field(default_factory=list)


# --- Commands ---
@dataclass
class CommandDecl(ASTNode):
    name: str = ""
    prefixes: list[str] = field(default_factory=lambda: ["!"])
    aliases: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    permission_message: str = ""
    cooldown: str = ""
    description: str = ""
    usage: str = ""
    category: str = ""
    executable_in: str = "both"
    arguments: list[tuple[str, str, str]] = field(default_factory=list)
    trigger: list[Statement] = field(default_factory=list)


@dataclass
class SlashCommandDecl(ASTNode):
    name: str = ""
    description: str = ""
    bot: str = ""
    guild: str = ""
    arguments: list[SlashOption] = field(default_factory=list)
    cooldown: str = ""
    cooldown_body: list[Statement] = field(default_factory=list)
    enabled_for: list[str] = field(default_factory=list)
    disabled: bool = False
    trigger: list[Statement] = field(default_factory=list)
    subcommands: list[SlashCommandDecl] = field(default_factory=list)


@dataclass
class SlashOption(ASTNode):
    name: str = ""
    type: str = "string"
    description: str = ""
    required: bool = False
    choices: list[tuple[str, str]] = field(default_factory=list)
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    autocomplete: bool = False


# --- Events ---
@dataclass
class EventHandler(ASTNode):
    event_type: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    bot_filter: str = ""
    body: list[Statement] = field(default_factory=list)
    priority: int = 0


# --- Bot Definition ---
@dataclass
class BotDefinition(ASTNode):
    name: str = ""
    token: str = ""
    intents: list[str] = field(default_factory=list)
    policy: str = "all"
    cache_flags: str = "default"
    compression: str = "none"
    auto_reconnect: bool = True
    force_reload: bool = False
    events: list[EventHandler] = field(default_factory=list)


# --- Builder Sections ---
@dataclass
class EmbedBuilder(ASTNode):
    title: Expression | None = None
    description: Expression | None = None
    color: Expression | None = None
    author: Expression | None = None
    author_icon: Expression | None = None
    author_url: Expression | None = None
    image: Expression | None = None
    thumbnail: Expression | None = None
    footer: Expression | None = None
    footer_icon: Expression | None = None
    title_url: Expression | None = None
    timestamp: Expression | None = None
    fields: list[tuple[Expression, Expression, bool]] = field(default_factory=list)
    store_in: str = ""


@dataclass
class ComponentRowBuilder(ASTNode):
    components: list[Expression] = field(default_factory=list)
    store_in: str = ""


@dataclass
class MessageBuilder(ASTNode):
    content: Expression | None = None
    embeds: list[EmbedBuilder] = field(default_factory=list)
    components: list[ComponentRowBuilder] = field(default_factory=list)
    attachments: list[Any] = field(default_factory=list)
    silent: bool = False
    store_in: str = ""


@dataclass
class ModalBuilder(ASTNode):
    title: Expression | None = None
    id: str = ""
    rows: list[Any] = field(default_factory=list)
    store_in: str = ""


@dataclass
class AudioLoadSection(ASTNode):
    source: Expression | None = None
    store_in: str = ""
    on_track_load: list[Statement] = field(default_factory=list)
    on_playlist_load: list[Statement] = field(default_factory=list)
    on_load_error: list[Statement] = field(default_factory=list)
    on_no_matches: list[Statement] = field(default_factory=list)


@dataclass
class MemberFilterSection(ASTNode):
    guild: Expression | None = None
    store_in: str = ""
    filter_var: str = ""
    body: list[Statement] = field(default_factory=list)


@dataclass
class WelcomeScreenModifier(ASTNode):
    guild: Expression | None = None
    description: Expression | None = None
    welcome_channels: list[tuple[Expression, Expression]] = field(default_factory=list)


# --- Type Declaration ---
@dataclass
class DiscordType(ASTNode):
    name: str = ""
    properties: dict[str, str] = field(default_factory=dict)
    base_type: str = ""
