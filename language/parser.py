from __future__ import annotations
from .lexer import Token, TokenType, Lexer
from .ast import *
from typing import Any, Optional


class ParseError(Exception):
    def __init__(self, message: str, token: Token | None = None, source_lines: list[str] | None = None):
        self.token = token
        self.source_lines = source_lines or []
        if token:
            base = f"Line {token.line}:{token.column}: {message}"
            if source_lines and 0 < token.line <= len(source_lines):
                ctx_start = max(0, token.line - 3)
                ctx_end = min(len(source_lines), token.line + 2)
                ctx = "\n".join(
                    f"{'>' if i + 1 == token.line else ' '} {i+1:4d} | {source_lines[i].rstrip()}"
                    for i in range(ctx_start, ctx_end)
                )
                super().__init__(f"{base}\n{ctx}")
            else:
                super().__init__(base)
        else:
            super().__init__(message)


class Parser:
    def __init__(self, source: str, filename: str = "<unknown>"):
        lexer = Lexer(source, filename)
        self.tokens = lexer.tokenize()
        self.pos = 0
        self.source_lines = source.splitlines(keepends=True) if source else []
        self._filename = filename

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    @property
    def filename(self) -> str:
        return self._filename

    def _error(self, message: str, token: Token | None = None) -> ParseError:
        return ParseError(message, token, self.source_lines)

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, *types: TokenType) -> Token:
        if self.peek().type not in types:
            expected = " or ".join(t.name for t in types)
            got = self.peek().type.name if self.peek() else "EOF"
            raise self._error(f"Expected {expected}, got {got}", self.peek())
        return self.advance()

    def match(self, *types: TokenType) -> Token | None:
        if self.peek().type in types:
            return self.advance()
        return None

    def skip_newlines(self) -> None:
        while self.peek().type == TokenType.NEWLINE:
            self.advance()

    def check_keyword(self, *words: str) -> bool:
        return self.peek().type == TokenType.KEYWORD and self.peek().value in words

    def match_name(self, *words: str) -> bool:
        return (self.peek().type in (TokenType.KEYWORD, TokenType.IDENTIFIER)) and self.peek().value in words

    def maybe_parse_bot_clause(self, ef: EffectStatement) -> None:
        if ef.keyword_args.get("bot"):
            return
        if self.check_keyword("with") and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "bot":
            self.advance()
            self.advance()
            self.match_keyword("named")
            ef.keyword_args["bot"] = self.parse_expression()

    def match_keyword(self, *words: str) -> Token | None:
        if self.check_keyword(*words):
            return self.advance()
        return None

    def expect_keyword(self, *words: str) -> Token:
        tok = self.peek()
        if not self.check_keyword(*words):
            raise self._error(f"Expected one of {words}, got {tok.value}", tok)
        return self.advance()

    def expect_name(self) -> Token:
        tok = self.peek()
        if tok.type not in (TokenType.IDENTIFIER, TokenType.KEYWORD):
            raise self._error(f"Expected identifier or keyword, got {tok.type.name} ({tok.value})", tok)
        return self.advance()

    def parse(self) -> Script:
        script = Script()
        self.skip_newlines()

        while self.peek().type != TokenType.EOF:
            if self.match_keyword("options"):
                self.expect(TokenType.COLON)
                self.skip_newlines()
                script.options = self.parse_options_block()
            elif self.match_keyword("variables"):
                self.expect(TokenType.COLON)
                self.skip_newlines()
                script.variables = self.parse_variables_block()
            elif self.check_keyword("local") and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "function":
                self.advance()
                fn = self.parse_function_decl()
                fn.local = True
                script.functions[fn.name] = fn
            elif self.check_keyword("function"):
                self.advance()
                fn = self.parse_function_decl()
                script.functions[fn.name] = fn
            elif self.check_keyword("define"):
                script.bot_definitions.append(self.parse_bot_definition())
            elif self.check_keyword("command") or self.check_keyword("discord"):
                script.commands.append(self.parse_command_decl())
            elif self.check_keyword("slash"):
                script.slash_commands.append(self.parse_slash_command_decl())
            elif self.check_keyword("on"):
                script.events.append(self.parse_event_handler())
            else:
                stmt = self.parse_statement()
                if stmt:
                    script.global_statements.append(stmt)
            self.skip_newlines()
        return script

    def parse_options_block(self) -> dict[str, Any]:
        opts: dict[str, Any] = {}
        while self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                key = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                self.expect(TokenType.COLON)
                self.skip_newlines()
                val = self.parse_expression()
                opts[key] = val
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
            break
        return opts

    def parse_variables_block(self) -> list[tuple[str, Any]]:
        vars_list: list[tuple[str, Any]] = []
        while self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                var_tok = self.expect(TokenType.GLOBAL_VAR)
                self.expect(TokenType.EQUAL)
                val = self.parse_expression()
                vars_list.append((var_tok.value, val))
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
            break
        return vars_list

    def parse_function_decl(self) -> FunctionDecl:
        fn = FunctionDecl()
        fn.name = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
        if self.match(TokenType.LPAREN):
            while self.peek().type != TokenType.RPAREN and self.peek().type != TokenType.EOF:
                param_name = self.expect_name().value
                self.expect(TokenType.COLON)
                param_type = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                default_val = None
                if self.match(TokenType.EQUAL):
                    default_val = self.parse_expression()
                fn.parameters.append((param_name, param_type, default_val))
                if self.peek().type == TokenType.COMMA:
                    self.advance()
            self.expect(TokenType.RPAREN)
        if self.match_keyword("::"):
            fn.return_type = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        fn.body = self.parse_block()
        return fn

    def parse_command_decl(self) -> CommandDecl:
        cmd = CommandDecl()
        if self.check_keyword("discord"):
            self.advance()
        if self.check_keyword("command"):
            self.advance()
            if self.match(TokenType.SLASH):
                pass

        name_tok = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.STRING)
        cmd.name = name_tok.value.strip("/")

        while self.match(TokenType.LBRACKET):
            while self.peek().type != TokenType.RBRACKET and self.peek().type != TokenType.EOF:
                if self.match(TokenType.LESS):
                    pass
                arg_name = self.expect_name().value
                if self.match(TokenType.GREATER):
                    pass
                arg_type = "text"
                if self.peek().type == TokenType.COLON:
                    self.advance()
                    arg_type = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                default = ""
                if self.match_keyword("="):
                    default = self.parse_expression()
                cmd.arguments.append((arg_name, arg_type, default))
                if self.peek().type == TokenType.COMMA:
                    self.advance()
            self.expect(TokenType.RBRACKET)

        self.expect(TokenType.COLON)
        self.skip_newlines()

        while self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                if self.check_keyword("prefixes"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.prefixes = self.parse_list_literal()
                elif self.check_keyword("aliases"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.aliases = self.parse_list_literal()
                elif self.check_keyword("permissions"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.permissions = self.parse_list_literal()
                elif self.check_keyword("permission", "message"):
                    self.advance()
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.permission_message = self.parse_expression()
                elif self.check_keyword("cooldown"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.cooldown = self.parse_expression()
                elif self.check_keyword("description"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.description = self.parse_expression()
                elif self.check_keyword("usage"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.usage = self.parse_expression()
                elif self.check_keyword("category"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    cmd.category = self.parse_expression()
                elif self.check_keyword("executable"):
                    self.advance()
                    self.expect(TokenType.KEYWORD, "in")
                    self.expect(TokenType.COLON)
                    cmd.executable_in = self.parse_expression()
                elif self.check_keyword("trigger"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    self.skip_newlines()
                    cmd.trigger = self.parse_block()
                    if self.peek().type == TokenType.DEDENT:
                        break
                else:
                    self.advance()
            self.expect(TokenType.DEDENT)
            break
        return cmd

    def parse_slash_command_decl(self) -> SlashCommandDecl:
        self.expect_keyword("slash", "command")
        cmd = SlashCommandDecl()
        name_parts = [self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value]
        while self.peek().type in (TokenType.IDENTIFIER, TokenType.KEYWORD) and self.peek().type != TokenType.COLON:
            name_parts.append(self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value)
        cmd.name = " ".join(name_parts)

        self.expect(TokenType.COLON)
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
            if self.check_keyword("description"):
                self.advance()
                self.expect(TokenType.COLON)
                cmd.description = self.parse_expression()
            elif self.check_keyword("bot"):
                self.advance()
                self.expect(TokenType.COLON)
                cmd.bot = self.parse_expression()
            elif self.check_keyword("guild"):
                self.advance()
                self.expect(TokenType.COLON)
                cmd.guild = self.parse_expression()
            elif self.check_keyword("arguments"):
                self.advance()
                self.expect(TokenType.COLON)
                self.skip_newlines()
                if self.peek().type == TokenType.INDENT:
                    self.expect(TokenType.INDENT)
                    while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                        cmd.arguments.append(self.parse_slash_option())
                        self.skip_newlines()
                    self.expect(TokenType.DEDENT)
            elif self.check_keyword("trigger"):
                self.advance()
                self.expect(TokenType.COLON)
                self.skip_newlines()
                cmd.trigger = self.parse_block()
                if self.peek().type == TokenType.DEDENT:
                    break
            else:
                self.advance()
        self.expect(TokenType.DEDENT)
        return cmd

    def parse_slash_option(self) -> SlashOption:
        opt = SlashOption()
        opt.name = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
        if self.peek().type == TokenType.COLON:
            self.advance()
            opt.type = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
        if self.match(TokenType.EQUAL) or self.match_keyword("="):
            val = self.parse_expression()
        self.skip_newlines()
        while self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT:
                if self.check_keyword("description"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    opt.description = self.parse_expression()
                elif self.check_keyword("required"):
                    self.advance()
                    self.expect(TokenType.COLON)
                    opt.required = self.parse_expression()
                elif self.check_keyword("autocomplete"):
                    self.advance()
                    if self.match_keyword("from"):
                        self.advance()  # skip function reference (stored as name)
                    opt.autocomplete = True
                elif self.check_keyword("min") or self.check_keyword("max"):
                    is_min = self.advance().value == "min"
                    if self.match_keyword("value"):
                        pass
                    self.expect(TokenType.COLON)
                    val = self.parse_expression()
                    if is_min:
                        opt.min_value = val
                    else:
                        opt.max_value = val
                else:
                    self.advance()
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
        return opt

    def parse_event_handler(self) -> EventHandler:
        ev = EventHandler()
        self.expect_keyword("on")
        parts: list[str] = []
        while self.peek().type != TokenType.COLON and self.peek().type != TokenType.EOF and self.peek().type != TokenType.NEWLINE:
            if self.peek().type == TokenType.KEYWORD and self.peek().value == "from" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "bot":
                self.advance()
                self.advance()
                if self.peek().type == TokenType.STRING:
                    ev.bot_filter = self.advance().value
                elif self.peek().type == TokenType.IDENTIFIER or self.peek().type == TokenType.KEYWORD:
                    ev.bot_filter = self.advance().value
            elif self.peek().type == TokenType.KEYWORD and self.peek().value == "in":
                self.advance()
                ev.filters["in"] = self.parse_expression()
            elif self.peek().type == TokenType.PERCENT:
                self.advance()
                type_name = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                self.expect(TokenType.PERCENT)
                ev.filters["type"] = type_name
            else:
                tok = self.advance()
                if tok.value:
                    parts.append(tok.value)
        ev.event_type = " ".join(parts)
        self.expect(TokenType.COLON)
        self.skip_newlines()
        ev.body = self.parse_block()
        return ev

    def parse_bot_definition(self) -> BotDefinition:
        bd = BotDefinition()
        self.expect_keyword("define")
        self.match_keyword("new")
        self.expect_keyword("bot")
        self.match_keyword("named")
        bd.name = self.expect(TokenType.STRING).value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
            if self.check_keyword("token"):
                self.advance()
                self.expect(TokenType.COLON)
                bd.token = self.expect(TokenType.STRING).value
            elif self.check_keyword("intents"):
                self.advance()
                self.expect(TokenType.COLON)
                bd.intents = self.parse_list_literal()
            elif self.check_keyword("policy"):
                self.advance()
                self.expect(TokenType.COLON)
                bd.policy = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
            elif self.check_keyword("cache", "flags"):
                self.advance()
                self.advance()
                self.expect(TokenType.COLON)
                bd.cache_flags = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
            elif self.check_keyword("compression"):
                self.advance()
                self.expect(TokenType.COLON)
                bd.compression = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
            elif self.check_keyword("auto", "reconnect"):
                self.advance()
                self.advance()
                self.expect(TokenType.COLON)
                bd.auto_reconnect = self.parse_expression()
            elif self.check_keyword("force", "reload"):
                self.advance()
                self.advance()
                self.expect(TokenType.COLON)
                bd.force_reload = self.parse_expression()
            elif self.check_keyword("on"):
                ev = self.parse_event_handler()
                bd.events.append(ev)
                continue
            else:
                self.advance()
            self.skip_newlines()
        self.expect(TokenType.DEDENT)
        return bd

    def parse_block(self) -> list[Statement]:
        body: list[Statement] = []
        if self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
        return body

    def parse_statement(self) -> Statement | None:
        self.skip_newlines()
        if self.peek().type == TokenType.EOF or self.peek().type == TokenType.DEDENT:
            _pv = None

        _pv = None
        tok = self.peek()

        if tok.type == TokenType.KEYWORD:
            kw = tok.value
            if kw == "set":
                _pv = self.parse_set_statement()
            elif kw == "add":
                _pv = self.parse_add_statement()
            elif kw == "remove":
                _pv = self.parse_remove_statement()
            elif kw == "delete":
                self.advance()
                _pv = DeleteVariable(variable=self.parse_expression())
            elif kw == "clear":
                self.advance()
                _pv = ClearVariable(variable=self.parse_expression())
            elif kw == "if":
                _pv = self.parse_if_statement()
            elif kw == "loop":
                _pv = self.parse_loop_statement()
            elif kw == "while":
                _pv = self.parse_while_statement()
            elif kw == "do" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "while":
                _pv = self.parse_do_while_statement()
            elif kw == "continue":
                self.advance()
                _pv = ContinueStatement()
            elif kw == "exit":
                self.advance()
                count = 1
                if self.peek().type == TokenType.NUMBER:
                    count = self.advance().value
                _pv = BreakStatement(count=count)
            elif kw == "return":
                self.advance()
                val = None
                if self.peek().type != TokenType.NEWLINE and self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                    val = self.parse_expression()
                _pv = ReturnStatement(value=val)
            elif kw == "wait":
                self.advance()
                _pv = WaitStatement(duration=self.parse_expression())
            elif kw == "halt":
                self.advance()
                self.expect_keyword("for")
                _pv = WaitStatement(duration=self.parse_expression())
            elif kw == "cancel" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "event":
                self.advance()
                self.advance()
                _pv = CancelEventStatement()
            elif kw == "uncancel":
                self.advance()
                self.expect_keyword("event")
                _pv = UncancelEventStatement()
            elif kw == "stop":
                self.advance()
                _pv = StopTriggerStatement()
            elif kw == "throw":
                self.advance()
                _pv = ThrowStatement(message=self.parse_expression())
            elif kw == "log":
                self.advance()
                val = self.parse_expression()
                _pv = EffectStatement(effect_type="log", arguments=[val])
            elif kw == "send":
                _pv = self.parse_send_effect()
            elif kw == "reply":
                _pv = self.parse_reply_effect()
            elif kw == "post":
                _pv = self.parse_post_effect()
            elif kw == "broadcast":
                self.advance()
                content = self.parse_expression()
                self.expect_keyword("to")
                target = self.parse_expression()
                _pv = EffectStatement(effect_type="broadcast", arguments=[content, target])
            elif kw == "forward":
                self.advance()
                msg = self.parse_expression()
                self.expect_keyword("to")
                target = self.parse_expression()
                _pv = EffectStatement(effect_type="forward", arguments=[msg, target])
            elif kw == "crosspost":
                self.advance()
                _pv = EffectStatement(effect_type="crosspost", arguments=[self.parse_expression()])
            elif kw == "pin":
                self.advance()
                _pv = EffectStatement(effect_type="pin", arguments=[self.parse_expression()])
            elif kw == "unpin":
                self.advance()
                _pv = EffectStatement(effect_type="unpin", arguments=[self.parse_expression()])
            elif kw == "purge":
                self.advance()
                count = self.parse_expression()
                self.match_keyword("messages")
                self.match_keyword("in")
                ch = self.parse_expression() if self.peek().type != TokenType.NEWLINE else None
                _pv = EffectStatement(effect_type="purge", arguments=[count, ch])
            elif kw == "edit":
                _pv = self.parse_edit_effect()
            elif kw == "kick":
                self.advance()
                member = self.parse_expression()
                reason = None
                if self.match_keyword("due", "to"):
                    reason = self.parse_expression()
                _pv = EffectStatement(effect_type="kick", arguments=[member, reason])
            elif kw == "ban":
                self.advance()
                member = self.parse_expression()
                reason = None
                delete_dur = None
                if self.match_keyword("due", "to"):
                    reason = self.parse_expression()
                if self.match_keyword("and", "delete"):
                    delete_dur = self.parse_expression()
                    self.match_keyword("worth")
                    self.match_keyword("of", "messages")
                _pv = EffectStatement(effect_type="ban", arguments=[member, reason, delete_dur])
            elif kw == "unban":
                self.advance()
                user = self.parse_expression()
                self.expect_keyword("from")
                guild = self.parse_expression()
                _pv = EffectStatement(effect_type="unban", arguments=[user, guild])
            elif kw == "timeout" or kw == "time":
                self.advance()
                if kw == "time":
                    self.expect_keyword("out")
                member = self.parse_expression()
                if self.match_keyword("for"):
                    duration = self.parse_expression()
                    reason = None
                    if self.match_keyword("for"):
                        reason = self.parse_expression()
                    _pv = EffectStatement(effect_type="timeout", arguments=[member, duration, reason])
                elif self.match_keyword("until"):
                    until = self.parse_expression()
                    reason = None
                    if self.match_keyword("for"):
                        reason = self.parse_expression()
                    _pv = EffectStatement(effect_type="timeout_until", arguments=[member, until, reason])
                _pv = EffectStatement(effect_type="timeout", arguments=[member, None, None])
            elif kw == "remove" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "timeout":
                self.advance()
                self.advance()
                self.expect_keyword("from")
                member = self.parse_expression()
                _pv = EffectStatement(effect_type="remove_timeout", arguments=[member])
            elif kw == "move":
                self.advance()
                member = self.parse_expression()
                self.expect_keyword("to")
                channel = self.parse_expression()
                _pv = EffectStatement(effect_type="move_member", arguments=[member, channel])
            elif kw == "disconnect":
                self.advance()
                member = self.parse_expression()
                self.match_keyword("from")
                self.match_keyword("voice")
                _pv = EffectStatement(effect_type="disconnect_member", arguments=[member])
            elif kw == "mute":
                self.advance()
                member = self.parse_expression()
                _pv = EffectStatement(effect_type="mute_member", arguments=[member])
            elif kw == "unmute":
                self.advance()
                member = self.parse_expression()
                _pv = EffectStatement(effect_type="unmute_member", arguments=[member])
            elif kw == "deafen":
                self.advance()
                member = self.parse_expression()
                _pv = EffectStatement(effect_type="deafen_member", arguments=[member])
            elif kw == "undeafen":
                self.advance()
                member = self.parse_expression()
                _pv = EffectStatement(effect_type="undeafen_member", arguments=[member])
            elif kw == "create":
                _pv = self.parse_create_effect()
            elif kw == "make":
                _pv = self.parse_make_effect()
            elif kw == "connect":
                self.advance()
                bot = self.parse_expression()
                self.match_keyword("to")
                self.match_keyword("voice")
                self.match_keyword("channel")
                channel = self.parse_expression()
                _pv = EffectStatement(effect_type="connect_voice", arguments=[bot, channel])
            elif kw == "load":
                self.advance()
                self.expect_keyword("audio")
                self.expect_keyword("from")
                _pv = self.parse_audio_load_section()
            elif kw == "play" or kw == "force":
                is_force = kw == "force"
                if is_force:
                    self.advance()
                    self.match_keyword("play")
                else:
                    self.advance()
                self.match_keyword("the")
                self.match_keyword("track")
                track = self.parse_expression()
                self.match_keyword("the")
                self.match_keyword("first")
                self.match_keyword("track")
                self.match_keyword("of")
                self.match_keyword("the")
                self.match_keyword("queue")
                guild = None
                if self.match_keyword("in"):
                    guild = self.parse_expression()
                bot = None
                self.match_keyword("with", "bot")
                if self.peek().type == TokenType.STRING or self.peek().type == TokenType.IDENTIFIER:
                    bot = self.parse_expression()
                _pv = EffectStatement(effect_type="play_track", arguments=[track, guild, bot], keyword_args={"force": is_force})
            elif kw in ("pause", "resume", "skip", "stop"):
                _pv = self.parse_audio_control(kw)
            elif kw == "set" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value in ("volume", "repeat", "auto", "audio"):
                self.advance()
                _pv = self.parse_audio_set(kw)
            elif kw == "defer":
                self.advance()
                self.match_keyword("the", "interaction")
                _pv = EffectStatement(effect_type="defer_interaction")
            elif kw == "shutdown":
                self.advance()
                self.match_keyword("bot")
                bot = self.parse_expression() if self.peek().type != TokenType.NEWLINE else None
                _pv = EffectStatement(effect_type="shutdown_bot", arguments=[bot])
            elif kw == "trigger":
                _pv = self.parse_trigger_custom_event()
            elif kw == "webhook":
                _pv = self.parse_webhook_effect()
            elif kw == "retrieve":
                _pv = self.parse_retrieve_effect()
            elif kw == "register":
                _pv = self.parse_register_effect()
            elif kw == "show":
                self.advance()
                modal = self.parse_expression()
                self.expect_keyword("to")
                self.match_keyword("the")
                user = self.parse_expression()
                _pv = EffectStatement(effect_type="show_modal", arguments=[modal, user])
            elif kw == "execute":
                _pv = self.parse_execute_effect()
            elif kw == "set" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "presence":
                self.advance()
                self.advance()
                self.expect_keyword("of")
                bot = self.parse_expression()
                self.expect_keyword("to")
                activity_type = self.expect(TokenType.KEYWORD).value
                text = self.parse_expression()
                _pv = EffectStatement(effect_type="set_presence", arguments=[bot, activity_type, text])
            elif kw == "set" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "online":
                self.advance()
                self.advance()
                self.expect_keyword("status")
                self.expect_keyword("of")
                bot = self.parse_expression()
                self.expect_keyword("to")
                status = self.parse_expression()
                _pv = EffectStatement(effect_type="set_status", arguments=[bot, status])
            elif kw == "load" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "members":
                self.advance()
                self.advance()
                self.expect_keyword("of")
                guild = self.parse_expression()
                _pv = EffectStatement(effect_type="load_members", arguments=[guild])
            elif kw == "send" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "typing":
                self.advance()
                self.advance()
                self.match_keyword("in")
                channel = self.parse_expression()
                _pv = EffectStatement(effect_type="send_typing", arguments=[channel])
            elif kw == "update":
                self.advance()
                cmd = self.parse_expression()
                self.match_keyword("globally")
                self.match_keyword("in")
                bot = self.parse_expression() if self.peek().type != TokenType.NEWLINE else None
                _pv = EffectStatement(effect_type="update_command", arguments=[cmd, bot])
            elif kw == "reply" and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "with":
                _pv = self.parse_reply_effect()

        # Try to parse as expression (could be function call or property access)
        if _pv is None and tok.type in (TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.STRING, TokenType.NUMBER, TokenType.HEX_COLOR, TokenType.GLOBAL_VAR, TokenType.LOCAL_VAR, TokenType.OPTION_VAR, TokenType.BOOLEAN):
            expr = self.parse_expression()
            if self.check_keyword("if") and self.peek(1).type != TokenType.KEYWORD:
                pass
            if isinstance(expr, FunctionCall):
                stmt = EffectStatement(effect_type="call_function", arguments=[expr])
            else:
                stmt = EffectStatement(effect_type="expression", arguments=[expr])
            _pv = stmt
        if _pv is not None and isinstance(_pv, EffectStatement):
            self.maybe_parse_bot_clause(_pv)
        _pv = _pv
        _pv = _pv
        return _pv

    def parse_set_statement(self) -> Statement:
        self.advance()
        var = self.parse_expression()
        if isinstance(var, PropertyAccess) and var.property_name in ("cooldown", "cooldown_message", "cooldown_bypass"):
            if self.match_keyword("to"):
                val = self.parse_expression()
                return EffectStatement(effect_type=f"set_{var.property_name}", arguments=[var.obj, val])
            self.expect(TokenType.EQUAL)
            val = self.parse_expression()
            return EffectStatement(effect_type=f"set_{var.property_name}", arguments=[var.obj, val])
        if isinstance(var, PropertyAccess) and var.property_name in ("prefix", "prefixes"):
            if self.match_keyword("to"):
                val = self.parse_expression()
                return EffectStatement(effect_type="set_prefix", arguments=[var.obj, val])
            self.expect(TokenType.EQUAL)
            val = self.parse_expression()
            return EffectStatement(effect_type="set_prefix", arguments=[var.obj, val])
        if self.match_keyword("to"):
            val = self.parse_expression()
            return SetVariable(variable=var, value=val)
        self.expect(TokenType.EQUAL)
        val = self.parse_expression()
        return SetVariable(variable=var, value=val)

    def parse_add_statement(self) -> AddToVariable:
        self.advance()
        val = self.parse_expression()
        if self.match_keyword("to"):
            var = self.parse_expression()
            return AddToVariable(variable=var, value=val)
        return AddToVariable(value=val)

    def parse_remove_statement(self) -> RemoveFromVariable:
        self.advance()
        val = self.parse_expression()
        if self.match_keyword("from"):
            var = self.parse_expression()
            return RemoveFromVariable(variable=var, value=val)
        return RemoveFromVariable(value=val)

    def parse_if_statement(self) -> IfStatement:
        stmt = IfStatement()
        self.advance()
        stmt.condition = self.parse_expression()
        self.expect(TokenType.COLON)
        self.skip_newlines()
        stmt.body = self.parse_block()
        while self.check_keyword("else"):
            self.advance()
            if self.check_keyword("if"):
                self.advance()
                cond = self.parse_expression()
                self.expect(TokenType.COLON)
                self.skip_newlines()
                body = self.parse_block()
                stmt.elif_conditions.append((cond, body))
            else:
                self.expect(TokenType.COLON)
                self.skip_newlines()
                stmt.else_body = self.parse_block()
                break
        return stmt

    def parse_loop_statement(self) -> LoopStatement:
        stmt = LoopStatement()
        self.advance()
        if self.check_keyword("all"):
            self.advance()
            if self.check_keyword("members"):
                stmt.loop_type = "members"
                self.advance()
                self.match_keyword("in")
                stmt.iterable = self.parse_expression() if self.peek().type != TokenType.COLON else None
            elif self.check_keyword("guilds"):
                stmt.loop_type = "guilds"
                self.advance()
                self.match_keyword("of")
                stmt.iterable = self.parse_expression() if self.peek().type != TokenType.COLON else None
            elif self.check_keyword("channels"):
                stmt.loop_type = "channels"
                self.advance()
                self.match_keyword("in")
                stmt.iterable = self.parse_expression() if self.peek().type != TokenType.COLON else None
            elif self.check_keyword("roles"):
                stmt.loop_type = "roles"
                self.advance()
                stmt.iterable = None
            else:
                stmt.iterable = self.parse_expression()
        elif self.peek().type == TokenType.NUMBER and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "times":
            count = self.advance().value
            self.advance()
            stmt.loop_type = "times"
            stmt.max_iterations = count
        else:
            stmt.iterable = self.parse_expression()
            if self.check_keyword("and"):
                self.advance()
                stmt.iterable = BinaryOp(left=stmt.iterable, op="and", right=self.parse_expression())
        self.expect(TokenType.COLON)
        self.skip_newlines()
        stmt.body = self.parse_block()
        return stmt

    def parse_while_statement(self) -> WhileStatement:
        stmt = WhileStatement()
        self.advance()
        stmt.condition = self.parse_expression()
        self.expect(TokenType.COLON)
        self.skip_newlines()
        stmt.body = self.parse_block()
        return stmt

    def parse_do_while_statement(self) -> DoWhileStatement:
        stmt = DoWhileStatement()
        self.advance()
        self.advance()
        stmt.condition = self.parse_expression()
        self.expect(TokenType.COLON)
        self.skip_newlines()
        stmt.body = self.parse_block()
        return stmt

    def parse_create_effect(self) -> EffectStatement:
        self.advance()
        if self.check_keyword("new"):
            self.advance()
            ef = EffectStatement(effect_type="create")
            if self.check_keyword("role"):
                self.advance()
                ef.effect_type = "create_role"
                self.expect_keyword("named")
                ef.arguments.append(self.parse_expression())
                self.expect_keyword("in")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("and", "store"):
                    self.match_keyword("it")
                    self.match_keyword("in")
                    if self.peek().type == TokenType.LOCAL_VAR or self.peek().type == TokenType.GLOBAL_VAR:
                        ef.keyword_args["store_in"] = self.advance().value
            elif self.check_keyword("invite"):
                self.advance()
                ef.effect_type = "create_invite"
                self.expect_keyword("for")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("with", "max", "uses"):
                    ef.keyword_args["max_uses"] = self.parse_expression()
                if self.match_keyword("and", "max", "age"):
                    ef.keyword_args["max_age"] = self.parse_expression()
                if self.match_keyword("and", "store"):
                    self.match_keyword("it")
                    self.match_keyword("in")
                    if self.peek().type in (TokenType.LOCAL_VAR, TokenType.GLOBAL_VAR):
                        ef.keyword_args["store_in"] = self.advance().value
            elif self.check_keyword("emote"):
                self.advance()
                ef.effect_type = "create_emote"
                self.expect_keyword("named")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("with"):
                    self.match_keyword("url")
                    self.match_keyword("path")
                    ef.arguments.append(self.parse_expression())
                self.expect_keyword("in")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("and", "store"):
                    self.match_keyword("it")
                    self.match_keyword("in")
                    ef.keyword_args["store_in"] = self.advance().value
            elif self.check_keyword("sticker"):
                self.advance()
                ef.effect_type = "create_sticker"
                self.expect_keyword("named")
                ef.arguments.append(self.parse_expression())
                self.expect_keyword("with", "description")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("and"):
                    self.match_keyword("url")
                    self.match_keyword("path")
                    ef.arguments.append(self.parse_expression())
                self.expect_keyword("with", "emoji")
                ef.arguments.append(self.parse_expression())
                self.expect_keyword("in")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("and", "store"):
                    self.match_keyword("it")
                    self.match_keyword("in")
                    ef.keyword_args["store_in"] = self.advance().value
            elif self.check_keyword("post") or self.check_keyword("thread"):
                ef.effect_type = "create_forum_post" if self.peek().value == "post" else "create_thread"
                self.advance()
                self.expect_keyword("named")
                ef.arguments.append(self.parse_expression())
                self.expect_keyword("in")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("from", "message"):
                    ef.keyword_args["from_message"] = self.parse_expression()
                if self.match_keyword("with", "content"):
                    ef.keyword_args["content"] = self.parse_expression()
                if self.match_keyword("with", "tags"):
                    ef.keyword_args["tags"] = self.parse_expression()
                if self.match_keyword("and", "store"):
                    self.match_keyword("it")
                    self.match_keyword("in")
                    ef.keyword_args["store_in"] = self.advance().value
            elif self.check_keyword("poll"):
                self.advance()
                self.match_keyword("named")
                ef.effect_type = "create_poll"
                ef.arguments.append(self.parse_expression())
                self.match_keyword("in")
                ef.arguments.append(self.parse_expression())
                if self.match_keyword("with", "options"):
                    options = []
                    options.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        options.append(self.parse_expression())
                    ef.keyword_args["options"] = options
                if self.match_keyword("lasting") or self.match_keyword("for"):
                    ef.keyword_args["duration"] = self.parse_expression()
                if self.match_keyword("and", "store"):
                    self.match_keyword("it")
                    self.match_keyword("in")
                    if self.peek().type in (TokenType.LOCAL_VAR, TokenType.GLOBAL_VAR):
                        ef.keyword_args["store_in"] = self.advance().value
            elif self.check_keyword("scheduled") or self.check_keyword("guild", "scheduled"):
                self.match_keyword("guild")
                self.match_keyword("scheduled")
                ef.effect_type = "create_scheduled_event"
                self.expect_keyword("named")
                ef.arguments.append(self.parse_expression())
                self.expect_keyword("in")
                ef.arguments.append(self.parse_expression())
                self.match_keyword("starting")
                ef.keyword_args["start"] = self.parse_expression()
                if self.match_keyword("ending"):
                    ef.keyword_args["end"] = self.parse_expression()
                if self.match_keyword("with", "description"):
                    ef.keyword_args["description"] = self.parse_expression()
                if self.match_keyword("and", "store"):
                    self.match_keyword("it")
                    self.match_keyword("in")
                    ef.keyword_args["store_in"] = self.advance().value
            else:
                ef.arguments.append(self.parse_expression())
            return ef
        ef = EffectStatement(effect_type="create")
        ef.arguments.append(self.parse_expression())
        return ef

    def parse_make_effect(self) -> EffectStatement:
        self.advance()
        if self.check_keyword("new"):
            self.advance()
        self.match_keyword("discord")
        self.match_keyword("message")

        if self.check_keyword("embed"):
            self.advance()
            return self.parse_embed_builder()
        elif self.check_keyword("component") or self.check_keyword("components"):
            self.advance()
            if self.peek().type == TokenType.KEYWORD and self.peek().value == "row":
                self.advance()
            return self.parse_component_row_builder()
        elif self.check_keyword("container"):
            return self.parse_container_builder()
        elif self.check_keyword("row"):
            self.advance()
            return self.parse_component_row_builder()
        else:
            ef = EffectStatement(effect_type="make")
            ef.arguments.append(self.parse_expression())
            return ef

    def parse_embed_builder(self) -> EffectStatement:
        ef = EffectStatement(effect_type="make_embed")
        if self.match_keyword("using", "template"):
            ef.keyword_args["template"] = self.parse_expression()
        if self.match_keyword("and", "store"):
            self.match_keyword("it")
            self.match_keyword("in")
            ef.keyword_args["store_in"] = self.advance().value if self.peek().type in (TokenType.LOCAL_VAR, TokenType.GLOBAL_VAR) else ""
        self.expect(TokenType.COLON)
        self.skip_newlines()
        ef.body = []
        if self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                if self.check_keyword("set"):
                    self.advance()
                    prop_token = self.advance()
                    prop_name = prop_token.value
                    next_tok = self.peek()
                    if next_tok.type == TokenType.KEYWORD and next_tok.value == "of":
                        self.advance()
                        if self.check_keyword("embed"):
                            self.advance()
                    if prop_name == "embed" and self.peek().type == TokenType.KEYWORD and self.peek().value == "color":
                        self.advance()
                        prop_name = "color"
                        if self.check_keyword("of"):
                            self.advance()
                            if self.check_keyword("embed"):
                                self.advance()
                    if prop_name == "title" and self.check_keyword("url"):
                        self.advance()
                        prop_name = "title_url"
                        if self.check_keyword("of"):
                            self.advance()
                            if self.check_keyword("embed"):
                                self.advance()
                    if prop_name == "author":
                        if self.check_keyword("icon"):
                            self.advance()
                            prop_name = "author_icon"
                            if self.check_keyword("of"):
                                self.advance()
                                if self.check_keyword("embed"):
                                    self.advance()
                        elif self.check_keyword("url"):
                            self.advance()
                            prop_name = "author_url"
                            if self.check_keyword("of"):
                                self.advance()
                                if self.check_keyword("embed"):
                                    self.advance()
                    if prop_name == "footer":
                        if self.check_keyword("icon"):
                            self.advance()
                            prop_name = "footer_icon"
                            if self.check_keyword("of"):
                                self.advance()
                                if self.check_keyword("embed"):
                                    self.advance()
                    if prop_name == "embed" and self.check_keyword("color"):
                        self.advance()
                        prop_name = "color"
                        if self.check_keyword("of"):
                            self.advance()
                            if self.check_keyword("embed"):
                                self.advance()
                    if self.check_keyword("to"):
                        self.advance()
                    val = self.parse_expression()
                    ef.body.append(EffectStatement(effect_type="embed_set_" + prop_name, arguments=[val]))
                elif self.check_keyword("add"):
                    self.advance()
                    inline = False
                    if self.check_keyword("inline"):
                        self.advance()
                        inline = True
                    self.match_keyword("field")
                    self.expect_keyword("named")
                    name = self.parse_expression()
                    self.expect_keyword("with")
                    self.match_keyword("value")
                    val = self.parse_expression()
                    self.match_keyword("to")
                    self.match_keyword("fields")
                    self.match_keyword("of")
                    self.match_keyword("embed")
                    ef.body.append(EffectStatement(effect_type="embed_add_field", arguments=[name, val, inline]))
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
        return ef

    def parse_component_row_builder(self) -> EffectStatement:
        ef = EffectStatement(effect_type="make_row")
        if self.match_keyword("and", "store"):
            self.match_keyword("it")
            self.match_keyword("in")
            if self.peek().type in (TokenType.LOCAL_VAR, TokenType.GLOBAL_VAR):
                ef.keyword_args["store_in"] = self.advance().value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        ef.body = []
        if self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT and self.peek().type != TokenType.EOF:
                if self.check_keyword("add"):
                    self.advance()
                    component = self.parse_expression()
                    self.match_keyword("to")
                    self.match_keyword("components")
                    self.match_keyword("of")
                    self.match_keyword("the")
                    self.match_keyword("row")
                    self.match_keyword("builder")
                    ef.body.append(EffectStatement(effect_type="row_add_component", arguments=[component]))
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
        return ef

    def parse_container_builder(self) -> EffectStatement:
        ef = EffectStatement(effect_type="make_container")
        if self.match_keyword("with"):
            if self.match_keyword("unique"):
                pass
            self.match_keyword("id")
            ef.keyword_args["id"] = self.parse_expression().value
        if self.match_keyword("and", "store"):
            self.match_keyword("it")
            self.match_keyword("in")
            ef.keyword_args["store_in"] = self.advance().value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        ef.body = self.parse_block() if self.peek().type == TokenType.INDENT else []
        return ef

    def parse_trigger_custom_event(self) -> EffectStatement:
        self.advance()
        self.match_keyword("custom")
        self.expect_keyword("event")
        ef = EffectStatement(effect_type="trigger_custom_event")
        ef.arguments.append(self.parse_expression())
        if self.match_keyword("with", "data"):
            data = self.parse_expression()
            ef.keyword_args["data"] = data
        return ef

    def parse_register_effect(self) -> EffectStatement:
        self.advance()
        if self.check_keyword("embed"):
            self.advance()
            self.match_keyword("template")
            ef = EffectStatement(effect_type="register_embed_template")
            ef.arguments.append(self.parse_expression())
            self.expect(TokenType.COLON)
            self.skip_newlines()
            ef.body = []
            if self.peek().type == TokenType.INDENT:
                self.expect(TokenType.INDENT)
                while self.peek().type != TokenType.DEDENT:
                    ef.body.append(self.parse_statement())
                    self.skip_newlines()
                self.expect(TokenType.DEDENT)
            return ef
        elif self.check_keyword("webhook"):
            self.advance()
            ef = EffectStatement(effect_type="register_webhook")
            self.expect_keyword("client", "named")
            ef.arguments.append(self.parse_expression())
            self.expect_keyword("with", "url")
            ef.arguments.append(self.parse_expression())
            if self.match_keyword("and", "store"):
                self.match_keyword("it")
                self.match_keyword("in")
                ef.keyword_args["store_in"] = self.advance().value
            return ef
        ef = EffectStatement(effect_type="register")
        ef.arguments.append(self.parse_expression())
        return ef

    def parse_retrieve_effect(self) -> EffectStatement:
        self.advance()
        ef = EffectStatement(effect_type="retrieve")
        if self.check_keyword("member"):
            self.advance()
            ef.effect_type = "retrieve_member"
            self.expect_keyword("with", "id")
            ef.arguments.append(self.parse_expression())
            self.match_keyword("in")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
        elif self.check_keyword("message") and not self.check_keyword("messages"):
            self.advance()
            ef.effect_type = "retrieve_message"
            self.expect_keyword("with", "id")
            ef.arguments.append(self.parse_expression())
            self.match_keyword("in")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
        elif self.check_keyword("messages"):
            self.advance()
            ef.effect_type = "retrieve_messages"
            self.match_keyword("in")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
            if self.match_keyword("limit"):
                ef.keyword_args["limit"] = self.parse_expression()
        elif self.check_keyword("user"):
            self.advance()
            ef.effect_type = "retrieve_user"
            self.expect_keyword("with", "id")
            ef.arguments.append(self.parse_expression())
        elif self.check_keyword("channel"):
            self.advance()
            ef.effect_type = "retrieve_channel"
            self.expect_keyword("with", "id")
            ef.arguments.append(self.parse_expression())
        elif self.check_keyword("bans"):
            self.advance()
            ef.effect_type = "retrieve_bans"
            self.match_keyword("in")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
        elif self.check_keyword("invites"):
            self.advance()
            ef.effect_type = "retrieve_invites"
            self.match_keyword("in")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
        elif self.check_keyword("webhooks"):
            self.advance()
            ef.effect_type = "retrieve_webhooks"
            self.match_keyword("in")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
        elif self.check_keyword("owner"):
            self.advance()
            ef.effect_type = "retrieve_owner"
            self.match_keyword("of")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
        elif self.check_keyword("audit", "logs"):
            self.advance()
            self.advance()
            ef.effect_type = "retrieve_audit_logs"
            self.match_keyword("in")
            if self.peek().type != TokenType.NEWLINE:
                ef.arguments.append(self.parse_expression())
        elif self.check_keyword("thread", "members"):
            self.advance()
            self.advance()
            ef.effect_type = "retrieve_thread_members"
            self.match_keyword("in")
            ef.arguments.append(self.parse_expression())

        if self.match_keyword("and", "store"):
            self.match_keyword("them" if "s" in ef.effect_type else "it")
            self.match_keyword("in")
            if self.peek().type in (TokenType.LOCAL_VAR, TokenType.GLOBAL_VAR):
                ef.keyword_args["store_in"] = self.advance().value
        return ef

    def parse_execute_effect(self) -> EffectStatement:
        self.advance()
        ef = EffectStatement(effect_type="execute")
        if self.match_keyword("as"):
            ef.keyword_args["as"] = self.parse_expression()
        else:
            ef.arguments.append(self.parse_expression())
        return ef

    def parse_edit_effect(self) -> EffectStatement:
        self.advance()
        ef = EffectStatement(effect_type="edit")

        if self.check_keyword("button"):
            self.advance()
            ef.effect_type = "edit_button"
            self.match_keyword("to", "show")
            ef.arguments.append(self.parse_expression())
            return ef
        if self.check_keyword("dropdown"):
            self.advance()
            ef.effect_type = "edit_dropdown"
            self.match_keyword("to", "show")
            ef.arguments.append(self.parse_expression())
            return ef
        if self.check_keyword("message") or self.check_keyword("the"):
            if self.check_keyword("the"):
                self.advance()
            self.match_keyword("message")
            self.match_keyword("components")
            ef.effect_type = "edit_components"
            self.match_keyword("to", "show")
            ef.arguments.append(self.parse_expression())
            return ef

        if self.check_keyword("message"):
            self.advance()
            msg = self.parse_expression()
            self.expect_keyword("to", "show")
            content = self.parse_expression()
            ef.effect_type = "edit_message"
            ef.arguments = [msg, content]
            return ef

        if self.check_keyword("the"):
            self.advance()
        message_types = ["message", "embed"]
        is_message = self.peek().value in message_types
        if is_message:
            self.advance()
        msg = self.parse_expression()
        self.expect_keyword("to", "show")
        content = self.parse_expression()
        ef.effect_type = "edit_message"
        ef.arguments = [msg, content]
        return ef

    def parse_webhook_effect(self) -> EffectStatement:
        self.advance()
        ef = EffectStatement(effect_type="webhook_send")
        if self.match_keyword("send") or self.match_keyword("post"):
            target = self.parse_expression()
            self.match_keyword("to")
            webhook = self.parse_expression()
            ef.arguments = [webhook, target]
        elif self.check_keyword("delete"):
            self.advance()
            ef.effect_type = "webhook_delete"
            ef.arguments.append(self.parse_expression())
        elif self.check_keyword("edit"):
            self.advance()
            ef.effect_type = "webhook_edit"
            ef.arguments.append(self.parse_expression())
            if self.match_keyword("name"):
                ef.keyword_args["name"] = self.parse_expression()
            if self.match_keyword("avatar"):
                ef.keyword_args["avatar"] = self.parse_expression()
        return ef

    def parse_send_effect(self) -> EffectStatement:
        self.advance()
        content = self.parse_expression()
        if self.match_keyword("to"):
            target = self.parse_expression()
            if isinstance(target, StringLiteral) and target.value == "console":
                ef = EffectStatement(effect_type="send_console", arguments=[content])
            else:
                ef = EffectStatement(effect_type="send", arguments=[content, target])
        else:
            ef = EffectStatement(effect_type="send", arguments=[content])
        self.maybe_parse_bot_clause(ef)
        return ef

    def parse_reply_effect(self) -> EffectStatement:
        self.advance()
        hidden = False
        if self.match_keyword("with"):
            if self.check_keyword("hidden"):
                self.advance()
                hidden = True
        content = self.parse_expression()
        ef = EffectStatement(effect_type="reply", arguments=[content], keyword_args={"hidden": hidden})
        if self.match_keyword("and", "store"):
            self.match_keyword("it")
            self.match_keyword("in")
            ef.keyword_args["store_in"] = self.advance().value
        self.maybe_parse_bot_clause(ef)
        return ef

    def parse_post_effect(self) -> EffectStatement:
        self.advance()
        ef = EffectStatement(effect_type="post")
        if self.check_keyword("last"):
            self.advance()
            self.match_keyword("embed")
            ef.effect_type = "post_last_embed"
            ef.arguments.append(IdentifierRef(name="last_embed"))
        else:
            ef.arguments.append(self.parse_expression())
        self.expect_keyword("to")
        ef.arguments.append(self.parse_expression())
        if self.check_keyword("with") and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "component":
            self.advance()
            self.advance()
            self.match_keyword("row")
            ef.keyword_args["component_row"] = self.parse_expression()
        self.maybe_parse_bot_clause(ef)
        return ef

    def parse_audio_load_section(self) -> EffectStatement:
        ef = EffectStatement(effect_type="load_audio")
        ef.arguments.append(self.parse_expression())
        if self.match_keyword("and", "store"):
            self.match_keyword("it")
            self.match_keyword("in")
            ef.keyword_args["store_in"] = self.advance().value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        ef.body = []
        if self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT:
                if self.check_keyword("on"):
                    subtype = None
                    self.advance()
                    n1 = self.peek().type == TokenType.KEYWORD and self.peek().value
                    n2 = self.peek(1).type == TokenType.KEYWORD and self.peek(1).value
                    if n1 == "track" and n2 == "load":
                        self.advance()
                        self.advance()
                        subtype = "track_load"
                    elif n1 == "playlist" and n2 == "load":
                        self.advance()
                        self.advance()
                        subtype = "playlist_load"
                    elif n1 == "load" and n2 == "error":
                        self.advance()
                        self.advance()
                        subtype = "load_error"
                    elif n1 == "no" and n2 == "matches":
                        self.advance()
                        self.advance()
                        subtype = "no_matches"
                    if subtype:
                        self.expect(TokenType.COLON)
                        self.skip_newlines()
                        body = self.parse_block()
                        ef.body.append(EffectStatement(effect_type="audio_" + subtype, arguments=[], keyword_args={}, body=body))
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
        return ef

    def parse_audio_control(self, kw: str) -> EffectStatement:
        ef = EffectStatement(effect_type=kw + "_track")
        self.match_keyword("the")
        self.match_keyword("audio")
        self.match_keyword("track")
        self.match_keyword("the")
        ef.arguments.append(self.parse_expression() if self.peek().type != TokenType.KEYWORD or self.peek().value not in ("in", "with") else None)
        self.match_keyword("in")
        ef.keyword_args["guild"] = self.parse_expression() if self.peek().type != TokenType.NEWLINE else None
        self.match_keyword("with", "bot")
        ef.keyword_args["bot"] = self.parse_expression() if self.peek().type != TokenType.NEWLINE else None
        if kw == "skip" and self.match_keyword("and", "store"):
            self.match_keyword("it")
            self.match_keyword("in")
            ef.keyword_args["store_in"] = self.advance().value
        return ef

    def parse_audio_set(self, kw: str) -> EffectStatement:
        ef = EffectStatement(effect_type="audio_set")
        if self.check_keyword("volume"):
            self.advance()
            ef.effect_type = "set_volume"
        elif self.check_keyword("repeat"):
            self.advance()
            ef.effect_type = "set_repeat"
        elif self.check_keyword("auto", "play"):
            self.advance()
            self.advance()
            ef.effect_type = "set_autoplay"
        elif self.check_keyword("audio"):
            self.advance()
            if self.check_keyword("pitch"):
                self.advance()
                ef.effect_type = "set_audio_pitch"
            elif self.check_keyword("speed"):
                self.advance()
                ef.effect_type = "set_audio_speed"
            elif self.check_keyword("rotation"):
                self.advance()
                ef.effect_type = "set_audio_rotation"
            elif self.check_keyword("mono"):
                self.advance()
                ef.effect_type = "set_audio_mono"
            elif self.check_keyword("volume"):
                self.advance()
                ef.effect_type = "set_audio_volume"
        self.expect_keyword("of")
        ef.arguments.append(self.parse_expression())
        self.expect_keyword("to")
        ef.arguments.append(self.parse_expression())
        return ef

    # --- Expression Parsing ---
    def parse_expression(self) -> Any:
        return self.parse_inline_conditional()

    def parse_inline_conditional(self) -> Any:
        expr = self.parse_or_expr()
        if self.match_keyword("if"):
            cond = self.parse_or_expr()
            false_val = None
            if self.match_keyword("else"):
                false_val = self.parse_or_expr()
            return InlineConditional(condition=cond, true_value=expr, false_value=false_val)
        if self.match(TokenType.QUESTION):
            default = self.parse_or_expr()
            return InlineConditional(condition=expr, true_value=expr, false_value=default)
        return expr

    def parse_or_expr(self) -> Any:
        left = self.parse_and_expr()
        while self.match_keyword("or"):
            right = self.parse_and_expr()
            left = BinaryOp(left=left, op="or", right=right)
        return left

    def parse_and_expr(self) -> Any:
        left = self.parse_comparison()
        while self.match_keyword("and"):
            right = self.parse_comparison()
            left = BinaryOp(left=left, op="and", right=right)
        return left

    def parse_comparison(self) -> Any:
        left = self.parse_addition()
        while True:
            if self.match(TokenType.EQUAL_EQUAL):
                right = self.parse_addition()
                left = BinaryOp(left=left, op="=", right=right)
            elif self.match(TokenType.NOT_EQUAL):
                right = self.parse_addition()
                left = BinaryOp(left=left, op="!=", right=right)
            elif self.match(TokenType.GREATER):
                right = self.parse_addition()
                left = BinaryOp(left=left, op=">", right=right)
            elif self.match(TokenType.GREATER_EQUAL):
                right = self.parse_addition()
                left = BinaryOp(left=left, op=">=", right=right)
            elif self.match(TokenType.LESS):
                right = self.parse_addition()
                left = BinaryOp(left=left, op="<", right=right)
            elif self.match(TokenType.LESS_EQUAL):
                right = self.parse_addition()
                left = BinaryOp(left=left, op="<=", right=right)
            elif self.check_keyword("is"):
                self.advance()
                if self.check_keyword("not"):
                    self.advance()
                    right = self.parse_addition()
                    left = BinaryOp(left=left, op="!=", right=right)
                elif self.check_keyword("set"):
                    self.advance()
                    left = UnaryOp(op="is_set", operand=left)
                elif self.check_keyword("between"):
                    self.advance()
                    low = self.parse_addition()
                    self.expect_keyword("and")
                    high = self.parse_addition()
                    left = BinaryOp(left=BinaryOp(left=left, op=">=", right=low), op="and", right=BinaryOp(left=left, op="<=", right=high))
                else:
                    right = self.parse_addition()
                    left = BinaryOp(left=left, op="=", right=right)
            elif self.check_keyword("contains"):
                self.advance()
                right = self.parse_addition()
                left = BinaryOp(left=left, op="contains", right=right)
            elif self.check_keyword("starts"):
                self.advance()
                if self.peek().value == "with":
                    self.advance()
                right = self.parse_addition()
                left = BinaryOp(left=left, op="starts_with", right=right)
            elif self.check_keyword("ends"):
                self.advance()
                if self.peek().value == "with":
                    self.advance()
                right = self.parse_addition()
                left = BinaryOp(left=left, op="ends_with", right=right)
            elif self.check_keyword("matches"):
                self.advance()
                right = self.parse_addition()
                left = BinaryOp(left=left, op="matches", right=right)
            else:
                break
        return left

    def parse_addition(self) -> Any:
        left = self.parse_multiplication()
        while True:
            if self.match(TokenType.PLUS):
                right = self.parse_multiplication()
                left = BinaryOp(left=left, op="+", right=right)
            elif self.match(TokenType.MINUS):
                right = self.parse_multiplication()
                left = BinaryOp(left=left, op="-", right=right)
            else:
                break
        return left

    def parse_multiplication(self) -> Any:
        left = self.parse_unary()
        while True:
            if self.match(TokenType.STAR):
                right = self.parse_unary()
                left = BinaryOp(left=left, op="*", right=right)
            elif self.match(TokenType.SLASH):
                right = self.parse_unary()
                left = BinaryOp(left=left, op="/", right=right)
            elif self.match(TokenType.CARET):
                right = self.parse_unary()
                left = BinaryOp(left=left, op="^", right=right)
            else:
                break
        return left

    def parse_unary(self) -> Any:
        if self.match(TokenType.MINUS):
            operand = self.parse_unary()
            return UnaryOp(op="-", operand=operand)
        if self.check_keyword("not"):
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op="not", operand=operand)
        return self.parse_primary()

    TIMESPAN_UNITS = {"second", "seconds", "minute", "minutes", "hour", "hours", "day", "days", "week", "weeks", "month", "months", "year", "years", "tick", "ticks", "millisecond", "milliseconds"}

    def parse_primary(self) -> Any:
        tok = self.peek()

        if tok.type == TokenType.NUMBER:
            self.advance()
            if self.peek().type == TokenType.KEYWORD and self.peek().value in self.TIMESPAN_UNITS:
                unit = self.advance().value
                return FunctionCall(name="timespan_from", arguments=[NumberLiteral(value=tok.value), StringLiteral(value=unit)], line=tok.line, column=tok.column)
            return NumberLiteral(value=tok.value, line=tok.line, column=tok.column)

        if tok.type == TokenType.HEX_COLOR:
            self.advance()
            return NumberLiteral(value=tok.value, line=tok.line, column=tok.column)

        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(value=tok.value, line=tok.line, column=tok.column)

        if tok.type == TokenType.BOOLEAN:
            self.advance()
            return BooleanLiteral(value=tok.value, line=tok.line, column=tok.column)

        if tok.type == TokenType.KEYWORD and tok.value == "null":
            self.advance()
            return NullLiteral()

        if tok.type == TokenType.GLOBAL_VAR:
            self.advance()
            v = Variable(name=tok.value, is_local=False, line=tok.line, column=tok.column)
            if self.peek().type == TokenType.COLON and self.peek(1).type == TokenType.COLON:
                self.advance()
                self.advance()
                index = self.parse_expression()
                return ListAccess(variable=v, index=index)
            if self.peek().type == TokenType.DOT:
                self.advance()
                prop = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                return PropertyAccess(obj=v, property_name=prop)
            if self.peek().type == TokenType.POSSESSIVE:
                self.advance()
                prop = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                return PropertyAccess(obj=v, property_name=prop)
            return v

        if tok.type == TokenType.LOCAL_VAR:
            self.advance()
            v = Variable(name=tok.value, is_local=True, line=tok.line, column=tok.column)
            if self.peek().type == TokenType.COLON and self.peek(1).type == TokenType.COLON:
                self.advance()
                self.advance()
                index = self.parse_expression()
                return ListAccess(variable=v, index=index)
            if self.peek().type == TokenType.DOT:
                self.advance()
                prop = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                return PropertyAccess(obj=v, property_name=prop)
            if self.peek().type == TokenType.POSSESSIVE:
                self.advance()
                prop = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                return PropertyAccess(obj=v, property_name=prop)
            return v

        if tok.type == TokenType.OPTION_VAR:
            self.advance()
            return Variable(name=tok.value, is_option=True, line=tok.line, column=tok.column)

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.LBRACKET:
            return self.parse_list_literal()

        if tok.type == TokenType.KEYWORD and tok.value == "new":
            return self.parse_new_expression()

        if tok.type == TokenType.KEYWORD and tok.value == "event" and self.peek(1).type == TokenType.MINUS:
            self.advance()
            self.advance()
            prop = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
            return Variable(name=f"event-{prop}", line=tok.line, column=tok.column)

        if tok.type == TokenType.IDENTIFIER or tok.type == TokenType.KEYWORD:
            ident = self.advance().value
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                args: list[Any] = []
                while self.peek().type != TokenType.RPAREN and self.peek().type != TokenType.EOF:
                    args.append(self.parse_expression())
                    if self.peek().type == TokenType.COMMA:
                        self.advance()
                self.expect(TokenType.RPAREN)
                return FunctionCall(name=ident, arguments=args, line=tok.line, column=tok.column)
            if self.peek().type == TokenType.PERCENT:
                self.advance()
                annotation = self.parse_expression() if self.peek().type != TokenType.PERCENT else None
                self.expect(TokenType.PERCENT)
                return Placeholder(type_name=ident)
            if self.peek().type == TokenType.DOT:
                self.advance()
                prop = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                return PropertyAccess(obj=IdentifierRef(name=ident), property_name=prop)
            if self.peek().type == TokenType.POSSESSIVE:
                self.advance()
                prop = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                return PropertyAccess(obj=IdentifierRef(name=ident), property_name=prop)
            if self.check_keyword("of"):
                self.advance()
                obj = self.parse_expression()
                return PropertyAccess(obj=obj, property_name=ident)
            if self.check_keyword("named"):
                self.advance()
                name = self.parse_expression()
                return FunctionCall(name=ident, arguments=[name])
            if self.check_keyword("with", "id"):
                self.advance()
                self.advance()
                id_val = self.parse_expression()
                return FunctionCall(name=ident, arguments=[id_val])
            if self.check_keyword("from"):
                self.advance()
                source = self.parse_expression()
                return PropertyAccess(obj=source, property_name=ident)
            return IdentifierRef(name=ident, line=tok.line, column=tok.column)

        if tok.type == TokenType.PERCENT:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.PERCENT)
            return expr

        if tok.type == TokenType.AT:
            self.advance()
            ident = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
            return IdentifierRef(name="@" + ident)

        raise self._error(f"Unexpected token: {tok.type.name} ({tok.value})", tok)

    def parse_new_expression(self) -> Any:
        self.advance()
        if self.match_keyword("embed"):
            return self.parse_embed_builder()
        if self.match_keyword("slash", "command"):
            return self.parse_inline_slash_command()
        if self.match_keyword("message"):
            return self.parse_inline_new_message()
        if self.match_keyword("modal"):
            return self.parse_inline_new_modal()
        if self.match_keyword("text", "input"):
            return self.parse_inline_new_text_input()
        if self.match_keyword("label"):
            return self.parse_inline_new_label()
        if self.match_keyword("container"):
            return self.parse_inline_new_container()
        if self.match_keyword("component", "row"):
            return self.parse_inline_component_row()

        # Check for button/dropdown by type keyword
        if self.check_keyword("button"):
            self.advance()
            return self.parse_inline_new_button()
        if self.check_keyword("dropdown"):
            self.advance()
            return self.parse_inline_new_dropdown()

        # Check for style + button/dropdown patterns (e.g. "primary button")
        style_kw = self.peek().value if self.peek().type in (TokenType.KEYWORD, TokenType.IDENTIFIER) else ""
        if style_kw in ("primary", "secondary", "success", "danger", "link") and self.peek(1).type == TokenType.KEYWORD and self.peek(1).value == "button":
            return self.parse_inline_new_button()

        type_name = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
        node = NewBuilder(type_name=type_name)
        self.expect(TokenType.COLON)
        self.skip_newlines()
        if self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            while self.peek().type != TokenType.DEDENT:
                key = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                self.expect(TokenType.COLON)
                val = self.parse_expression()
                node.properties[key] = val
                self.skip_newlines()
            self.expect(TokenType.DEDENT)
        return node

    def parse_inline_new_message(self) -> Any:
        node = NewBuilder(type_name="message")
        self.match_keyword("with")
        if self.peek().type == TokenType.COLON:
            self.advance()
            self.skip_newlines()
            if self.peek().type == TokenType.INDENT:
                self.expect(TokenType.INDENT)
                while self.peek().type != TokenType.DEDENT:
                    key = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                    self.expect(TokenType.COLON)
                    val = self.parse_expression()
                    node.properties[key] = val
                    self.skip_newlines()
                self.expect(TokenType.DEDENT)
        return node

    def parse_inline_new_modal(self) -> Any:
        self.match_keyword("with", "title")
        node = NewBuilder(type_name="modal")
        node.properties["title"] = self.parse_expression()
        self.match_keyword("and", "id")
        node.properties["id"] = self.parse_expression()
        if self.peek().type == TokenType.COLON:
            self.advance()
            self.skip_newlines()
            if self.peek().type == TokenType.INDENT:
                self.expect(TokenType.INDENT)
                while self.peek().type != TokenType.DEDENT:
                    key = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
                    self.expect(TokenType.COLON)
                    val = self.parse_expression()
                    node.properties[key] = val
                    self.skip_newlines()
                self.expect(TokenType.DEDENT)
        return node

    def parse_inline_new_button(self) -> Any:
        style = self.expect(TokenType.IDENTIFIER, TokenType.KEYWORD).value
        self.match_keyword("button")
        self.match_keyword("labeled")
        while self.check_keyword("with") or self.check_keyword("id"):
            self.advance()
        btn_id = self.parse_expression()
        self.match_keyword("named")
        label = self.parse_expression()
        node = NewBuilder(type_name="button")
        node.properties["style"] = StringLiteral(style)
        node.properties["id"] = btn_id
        node.properties["label"] = label
        if self.match_keyword("with", "reaction"):
            node.properties["emoji"] = self.parse_expression()
        return node

    def parse_inline_new_dropdown(self) -> Any:
        self.match_keyword("entity")
        is_entity = True
        self.match_keyword("dropdown")
        self.expect_keyword("with", "id")
        node = NewBuilder(type_name="entity_dropdown" if is_entity else "dropdown")
        node.properties["id"] = self.parse_expression()
        if self.match_keyword("targeting"):
            node.properties["target_types"] = self.parse_list_literal()
        return node

    def parse_inline_new_text_input(self) -> Any:
        self.expect_keyword("with", "id")
        node = NewBuilder(type_name="text_input")
        node.properties["id"] = self.parse_expression()
        self.match_keyword("named")
        if self.peek().type != TokenType.COLON and self.peek().type != TokenType.NEWLINE:
            node.properties["label"] = self.parse_expression()
        return node

    def parse_inline_new_label(self) -> Any:
        label_text = self.parse_expression()
        self.match_keyword("with")
        associated = self.parse_expression()
        node = NewBuilder(type_name="label")
        node.properties["text"] = label_text
        node.properties["associated"] = associated
        return node

    def parse_inline_slash_command(self) -> Any:
        node = NewBuilder(type_name="slash_command")
        self.match_keyword("named")
        node.properties["name"] = self.parse_expression()
        if self.match_keyword("with", "description"):
            node.properties["description"] = self.parse_expression()
        return node

    def parse_inline_new_container(self) -> Any:
        node = NewBuilder(type_name="container")
        if self.match_keyword("with"):
            if self.match_keyword("unique"):
                pass
            self.match_keyword("id")
            node.properties["id"] = self.parse_expression()
        if self.match_keyword("and", "store"):
            self.match_keyword("it")
            self.match_keyword("in")
            node.properties["store_in"] = self.advance().value
        self.expect(TokenType.COLON)
        self.skip_newlines()
        if self.peek().type == TokenType.INDENT:
            self.expect(TokenType.INDENT)
            node.children = self.parse_block()
            self.expect(TokenType.DEDENT)
        return node

    def parse_inline_component_row(self) -> Any:
        self.match_keyword("with")
        node = NewBuilder(type_name="component_row")
        components: list[Any] = []
        while self.peek().type != TokenType.NEWLINE and self.peek().type != TokenType.COLON and self.peek().type != TokenType.EOF:
            comp = self.parse_expression()
            components.append(comp)
            if self.match_keyword("and"):
                continue
            if self.match(TokenType.COMMA):
                continue
            break
        node.properties["components"] = components
        return node

    def parse_list_literal(self) -> list[Any]:
        items: list[Any] = []
        if self.match(TokenType.LBRACKET):
            while self.peek().type != TokenType.RBRACKET and self.peek().type != TokenType.EOF:
                items.append(self.parse_expression())
                if self.peek().type == TokenType.COMMA:
                    self.advance()
            self.expect(TokenType.RBRACKET)
        else:
            items.append(self.parse_expression())
            while self.match(TokenType.COMMA) or self.match_keyword("and"):
                items.append(self.parse_expression())
                if self.peek().type == TokenType.NEWLINE or self.peek().type == TokenType.DEDENT:
                    break
        return items


class IdentifierRef(Expression):
    def __init__(self, name: str = "", line: int = 0, column: int = 0):
        super().__init__()
        self.name = name
        self.line = line
        self.column = column
