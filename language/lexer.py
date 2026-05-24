from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TokenType(Enum):
    # Indentation
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()
    EOF = auto()

    # Literals
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    COLOR_NAME = auto()
    HEX_COLOR = auto()

    # Variables
    GLOBAL_VAR = auto()
    LOCAL_VAR = auto()
    OPTION_VAR = auto()

    # Identifiers & Keywords
    IDENTIFIER = auto()
    KEYWORD = auto()

    # Types / placeholders
    TYPE_PLACEHOLDER = auto()
    TYPE_ANNOTATION = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    PLUS_EQUAL = auto()
    MINUS_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    # Punctuation
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    PIPE = auto()

    # Special
    ARROW = auto()
    PERCENT = auto()
    HASH = auto()
    QUESTION = auto()
    AT = auto()
    DOLLAR = auto()
    TILDE = auto()
    NEW = auto()
    POSSESSIVE = auto()


KEYWORD_SET: frozenset[str] = frozenset({
    "on", "set", "to", "add", "remove", "delete", "clear", "create", "make",
    "new", "send", "reply", "post", "broadcast", "forward", "crosspost",
    "pin", "unpin", "purge", "edit", "kick", "ban", "unban", "timeout",
    "move", "disconnect", "mute", "unmute", "deafen", "undeafen",
    "load", "play", "stop", "pause", "resume", "skip", "queue",
    "if", "else", "else if", "then", "and", "or", "nor", "xor", "not",
    "loop", "while", "do", "continue", "exit", "return",
    "function", "local", "command", "slash", "discord",
    "options", "variables", "trigger", "prefixes",
    "with", "named", "in", "of", "from", "for", "as", "by",
    "is", "are", "has", "does", "have", "was",
    "contains", "starts", "ends", "matches",
    "true", "false", "null",
    "store", "show", "wait", "halt", "cancel", "uncancel",
    "throw", "log", "defer", "reply", "hidden",
    "embed", "button", "dropdown", "modal", "row", "component",
    "row", "section", "container", "text", "input",
    "update", "register", "clone", "join", "leave", "archive", "lock",
    "unlock", "connect", "loaded", "error", "failure",
    "any", "all", "chance", "between",
    "define", "bot", "intents", "policy", "cache", "flags",
    "compression", "auto", "reconnect", "force", "reload",
    "presence", "status", "online", "idle", "dnd", "invisible",
    "watching", "listening", "playing", "competing",
    "retrieve", "member", "user", "channel", "guild", "message",
    "role", "invite", "webhook", "sticker", "emoji", "emote",
    "trigger", "custom", "event", "data",
    "argument", "arguments", "permissions", "permission",
    "cooldown", "aliases", "description", "usage", "category",
    "executable", "private", "public",
    "enabled", "disabled",
    "where", "sorted", "ascending", "descending",
    "find", "filter", "var",
    "react", "response",
    "volume", "repeat", "auto", "pitch", "speed", "rotation",
    "mono",
    "first", "last", "random", "size", "index", "indices",
    "max", "min", "sum", "average",
    "round", "floor", "ceil",
    "absolute", "sqrt", "root", "sin", "cos", "tan",
    "length", "lowercase", "uppercase", "subtext", "trimmed",
    "replaced", "split", "joined",
    "parsed", "number", "integer", "text", "boolean",
    "now", "timespan", "date",
    "hex", "color",
    "template", "using",
    "autocomplete",
    "silent", "tts",
    "crosspost", "forwarded", "ephemeral",
    "spoiler", "animated",
    "owner", "boost", "booster",
    "everyone",
    "inviter",
    "voice", "stage", "news", "forum", "thread", "category",
    "copy", "paste",
    "bot", "bots",
    "export",
    "eval",
    "inspect", "debug", "simulate", "lint", "test",
    "overwrite",
    "afk",
    "welcome",
    "screen",
    "nsfw",
    "slowmode",
    "bitrate",
    "position",
    "parent",
    "topic",
    "tag", "tags", "post", "content",
    "title", "description", "color", "author", "footer", "image",
    "thumbnail", "timestamp", "field", "name", "value", "inline",
    "icon", "url", "fields", "rows", "components", "embed",
    "row", "button", "dropdown", "modal", "option", "options",
    "label", "placeholder", "required", "disabled", "style", "id",
    "emoji", "emote", "default", "min", "max", "range", "length",
    "named", "hidden", "silent", "target", "targets", "type",
    "placeholder", "required",
    "prefix", "suffix", "nickname", "nick",
    "status", "activity", "presence",
    "reason", "message", "messages",
    "channel", "channels", "guild", "guilds",
    "member", "members", "role", "roles", "user", "users",
    "event", "events", "command", "commands",
    "permission", "permissions",
    "cooldown", "cooldowns",
    "aliases", "alias",
    "executable", "category", "usage",
    "trigger", "triggers",
    "function", "functions",
    "variable", "variables",
    "bot", "bots", "token", "intents",
    "policy", "cache", "flags", "compression",
    "reconnect", "reload",
    "force", "auto",
    "online", "idle", "dnd", "invisible",
    "watching", "listening", "playing", "competing",
    "slash", "discord",
    "prefix", "prefixes",
    "text", "voice", "stage", "news", "forum", "thread",
    "category", "categories",
    "invite", "invites",
    "webhook", "webhooks",
    "sticker", "stickers",
    "scheduled", "scheduledevent",
    "emoji", "emojis", "emote", "emotes",
    "attachment", "attachments",
    "reaction", "reactions",
    "ban", "bans", "kick", "timeout", "times",
    "second", "seconds", "minute", "minutes",
    "hour", "hours", "day", "days",
    "week", "weeks", "month", "months",
    "year", "years", "tick", "ticks",
    "millisecond", "milliseconds",
    "mute", "unmute", "deafen", "undeafen",
    "move", "disconnect", "connect",
    "create", "delete", "edit", "clone",
    "archive", "unarchive", "lock", "unlock",
    "join", "leave", "add", "remove",
    "load", "play", "pause", "resume", "skip", "stop",
    "volume", "repeat", "pitch", "speed", "rotation", "mono",
    "queue", "track", "tracks", "playlist",
    "audio", "filter", "filters",
    "crosspost", "forward", "forwarded",
    "pin", "unpin", "purge",
    "defer", "interaction",
    "show", "send", "reply", "post", "broadcast",
    "set", "return", "wait", "halt",
    "if", "else", "then", "and", "or", "nor", "xor", "not",
    "loop", "while", "do", "continue", "exit",
    "stop", "throw", "log",
    "cancel", "uncancel",
    "retrieve", "find", "filter",
    "register", "update",
    "trigger", "custom",
    "execute",
    "make",
    "new",
    "any", "all", "chance", "between",
    "is", "are", "has", "does", "have", "was",
    "contains", "starts", "ends", "matches",
    "true", "false", "null",
    "parsed", "split", "joined",
    "first", "last", "random",
    "size", "index", "indices",
    "max", "min", "sum", "average",
    "round", "floor", "ceil",
    "absolute", "sqrt", "root", "sin", "cos", "tan",
    "length", "lowercase", "uppercase", "subtext", "trimmed",
    "replaced",
    "now", "timespan", "date",
    "hex", "color",
    "template", "using",
    "overwrite",
    "afk",
    "welcome", "screen",
    "nsfw", "slowmode", "bitrate", "position", "parent", "topic",
    "builder",
    "no", "yes",
    "primary", "secondary", "success", "danger", "link",
})


@dataclass(slots=True)
class Token:
    type: TokenType
    value: str | int | float | bool | None
    line: int
    column: int
    raw: str = ""

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.column})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"Line {line}:{column}: {message}")


class Lexer:
    def __init__(self, source: str, filename: str = "<unknown>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.indent_stack: list[int] = [0]
        self.at_line_start = True
        self.pending_dedents = 0

    def error(self, msg: str) -> LexerError:
        return LexerError(msg, self.line, self.column)

    def peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ""

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def skip_line(self) -> None:
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self.advance()

    def token(self, type_: TokenType, value: str | int | float | bool | None = None, raw: str = "") -> Token:
        t = Token(type_, value if value is not None else "", self.line, self.column - len(raw) if raw else self.column, raw)
        return t

    def add_token(self, type_: TokenType, value: str | int | float | bool | None = None, raw: str = "") -> None:
        self.tokens.append(self.token(type_, value, raw))

    def handle_indent(self, line_start: int) -> None:
        if line_start > self.indent_stack[-1]:
            self.indent_stack.append(line_start)
            self.add_token(TokenType.INDENT, line_start)
        elif line_start < self.indent_stack[-1]:
            while self.indent_stack and line_start < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.add_token(TokenType.DEDENT, line_start)
            if self.indent_stack and line_start != self.indent_stack[-1]:
                raise self.error(f"Indentation mismatch: expected {self.indent_stack[-1]} spaces, got {line_start}")

    def tokenize(self) -> list[Token]:
        i = 0
        while self.pos < len(self.source):
            ch = self.peek()
            start_col = self.column
            start_line = self.line

            if ch == "\n":
                self.advance()
                self.add_token(TokenType.NEWLINE)
                self.at_line_start = True
                continue

            if self.at_line_start:
                indent = 0
                while self.peek() == " ":
                    self.advance()
                    indent += 1
                if self.peek() == "\n" or self.peek() == "#" or self.peek() == "":
                    self.at_line_start = False
                    continue
                self.handle_indent(indent)
                self.at_line_start = False
                if self.peek() == "\n" or self.peek() == "#" or self.peek() == "":
                    continue
                ch = self.peek()
                start_col = self.column
                start_line = self.line

            if ch == "#":
                self.advance()
                hex_chars = ""
                peek_pos = 0
                while len(hex_chars) < 6 and self.peek(peek_pos) in "0123456789ABCDEFabcdef":
                    hex_chars += self.peek(peek_pos)
                    peek_pos += 1
                if len(hex_chars) == 6:
                    for _ in range(6):
                        self.advance()
                    self.add_token(TokenType.HEX_COLOR, int(hex_chars, 16))
                    continue
                self.skip_line()
                continue

            if ch == "'":
                if self.peek(1) == 's' and self.peek(2) != "'":
                    col = self.column
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.POSSESSIVE, "'s", self.line, col))
                    continue
                self.tokenize_string(ch)
                continue
            if ch == "\"":
                self.tokenize_string(ch)
                continue

            if ch.isdigit():
                self.tokenize_number()
                continue

            if ch == "\r":
                self.advance()
                continue

            if ch == " " or ch == "\t":
                self.advance()
                continue
                continue

            if ch == "$":
                self.advance()
                self.add_token(TokenType.DOLLAR)
                continue

            if ch == "#":
                self.advance()
                hex_chars = ""
                peek_pos = 0
                while len(hex_chars) < 6 and self.peek(peek_pos) in "0123456789ABCDEFabcdef":
                    hex_chars += self.peek(peek_pos)
                    peek_pos += 1
                if len(hex_chars) == 6:
                    for _ in range(6):
                        self.advance()
                    self.add_token(TokenType.HEX_COLOR, int(hex_chars, 16))
                    continue
                self.skip_line()
                continue

            if ch == "+":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    self.add_token(TokenType.PLUS_EQUAL)
                else:
                    self.add_token(TokenType.PLUS)
                continue

            if ch == "-":
                self.advance()
                self.add_token(TokenType.MINUS)
                continue

            if ch == "*":
                self.advance()
                self.add_token(TokenType.STAR)
                continue

            if ch == "/":
                self.advance()
                self.add_token(TokenType.SLASH)
                continue

            if ch == "=":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    self.add_token(TokenType.EQUAL_EQUAL)
                else:
                    self.add_token(TokenType.EQUAL)
                continue

            if ch == "!":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    self.add_token(TokenType.NOT_EQUAL)
                else:
                    self.add_token(TokenType.KEYWORD, "!")
                continue

            if ch == ">":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    self.add_token(TokenType.GREATER_EQUAL)
                else:
                    self.add_token(TokenType.GREATER)
                continue

            if ch == "<":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    self.add_token(TokenType.LESS_EQUAL)
                else:
                    self.add_token(TokenType.LESS)
                continue

            if ch == "&":
                self.advance()
                self.add_token(TokenType.KEYWORD, "&")
                continue

            if ch == ":":
                self.advance()
                self.add_token(TokenType.COLON)
                continue

            if ch == ",":
                self.advance()
                self.add_token(TokenType.COMMA)
                continue

            if ch == ".":
                self.advance()
                self.add_token(TokenType.DOT)
                continue

            if ch == "(":
                self.advance()
                self.add_token(TokenType.LPAREN)
                continue

            if ch == ")":
                self.advance()
                self.add_token(TokenType.RPAREN)
                continue

            if ch == "[":
                self.advance()
                self.add_token(TokenType.LBRACKET)
                continue

            if ch == "]":
                self.advance()
                self.add_token(TokenType.RBRACKET)
                continue

            if ch == "?":
                self.advance()
                self.add_token(TokenType.QUESTION)
                continue

            if ch == "{":
                self.advance()
                ch2 = self.peek()
                if ch2 == "}":
                    self.advance()
                    self.add_token(TokenType.LBRACE)
                    self.add_token(TokenType.RBRACE)
                    continue
                is_local = ch2 == "_"
                is_option = ch2 == "@"
                if is_local:
                    self.advance()
                elif is_option:
                    self.advance()

                name = ""
                while self.peek() not in ("}", ":", "\n", "\r", "") and not (self.peek() == ":" and self.peek(1) != ":"):
                    name += self.peek()
                    self.advance()

                if self.peek() == ":" and self.peek(1) == ":":
                    self.advance()
                    self.advance()
                    index_name = ""
                    while self.peek() not in ("}", "\n", "\r", ""):
                        index_name += self.peek()
                        self.advance()
                    full_name = f"{name}::{index_name}"
                    if is_local:
                        self.add_token(TokenType.LOCAL_VAR, f"_{full_name}")
                    elif is_option:
                        self.add_token(TokenType.OPTION_VAR, f"@{full_name}")
                    else:
                        self.add_token(TokenType.GLOBAL_VAR, full_name)
                else:
                    if is_local:
                        self.add_token(TokenType.LOCAL_VAR, f"_{name}")
                    elif is_option:
                        self.add_token(TokenType.OPTION_VAR, f"@{name}")
                    else:
                        self.add_token(TokenType.GLOBAL_VAR, name)

                if self.peek() == "}":
                    self.advance()
                continue

            if ch.isalpha() or ch == "_":
                self.tokenize_identifier()
                continue

            if ch == "%":
                self.advance()
                self.add_token(TokenType.PERCENT, "%")
                continue

            raise self.error(f"Unexpected character: {ch!r}")

        while self.indent_stack and self.indent_stack[-1] > 0:
            self.indent_stack.pop()
            self.add_token(TokenType.DEDENT, 0)

        self.add_token(TokenType.EOF)
        return self.tokens

    def tokenize_string(self, quote: str) -> None:
        start_line = self.line
        start_col = self.column
        self.advance()
        chars: list[str] = []
        while self.pos < len(self.source):
            ch = self.advance()
            if ch == "\\":
                if self.pos < len(self.source):
                    next_ch = self.advance()
                    if next_ch == "n":
                        chars.append("\n")
                    elif next_ch == "\\":
                        chars.append("\\")
                    elif next_ch == "\"":
                        chars.append("\"")
                    elif next_ch == "'":
                        chars.append("'")
                    elif next_ch == "t":
                        chars.append("\t")
                    elif next_ch == "r":
                        chars.append("\r")
                    elif next_ch == "0":
                        chars.append("\0")
                    elif next_ch == "%":
                        chars.append("%")
                    elif next_ch == "x" and self.peek(1) and self.peek(2):
                        hex_str = self.advance() + self.advance()
                        try:
                            chars.append(chr(int(hex_str, 16)))
                        except ValueError:
                            chars.append(f"\\x{hex_str}")
                    else:
                        chars.append("\\" + next_ch)
            elif ch == quote:
                self.add_token(TokenType.STRING, "".join(chars))
                return
            elif ch == "%":
                if self.peek() == "n" and self.peek(1) == "l" and self.peek(2) == "%":
                    self.advance()
                    self.advance()
                    self.advance()
                    chars.append("\n")
                elif self.peek() == "%":
                    self.advance()
                    chars.append("%")
                else:
                    chars.append("%")
            else:
                chars.append(ch)
        raise self.error(f"Unterminated string literal starting at line {start_line}")

    def tokenize_number(self) -> None:
        start = self.pos
        is_float = False
        while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == "."):
            if self.peek() == ".":
                if is_float:
                    break
                is_float = True
            self.advance()
        num_str = self.source[start:self.pos]
        if is_float:
            self.add_token(TokenType.NUMBER, float(num_str), num_str)
        else:
            self.add_token(TokenType.NUMBER, int(num_str), num_str)

    def tokenize_identifier(self) -> None:
        start = self.pos
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == "_"):
            self.advance()
        word = self.source[start:self.pos]

        if word in ("true", "True"):
            self.add_token(TokenType.BOOLEAN, True)
        elif word in ("false", "False"):
            self.add_token(TokenType.BOOLEAN, False)
        elif word in ("null", "none", "None"):
            self.add_token(TokenType.KEYWORD, "null")
        elif word in KEYWORD_SET:
            self.add_token(TokenType.KEYWORD, word)
        else:
            self.add_token(TokenType.IDENTIFIER, word)
