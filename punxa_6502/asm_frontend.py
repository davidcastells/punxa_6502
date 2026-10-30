"""Small, source-aware preprocessor for the ISA assembler's ca65 subset.

Includes, macros, constant conditionals and repetition cover the ISA sources'
preprocessing subset. Layout/data directives remain in the output so that the
assembler can validate them rather than silently discarding their effects.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import re
from typing import Sequence

from .asm_expressions import ExpressionError, evaluate


_IDENTIFIER = r"[A-Za-z_][A-Za-z_0-9]*"
_DIRECTIVE = re.compile(r"^(\.[A-Za-z_][A-Za-z_0-9]*)\b(.*)$")
_TOKEN = re.compile(
    r'''"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\$[0-9A-Fa-f]+|%[01]+|[0-9]+|[A-Za-z_][A-Za-z_0-9]*'''
)
_LABEL = re.compile(rf"^({_IDENTIFIER})\s*:\s*(.*)$")
_ASSIGNMENT = re.compile(rf"^({_IDENTIFIER})\s*=(?!=)")


@dataclass(frozen=True)
class SourceLine:
    """A logical source line and the original location of its text."""

    text: str
    filename: str
    line: int
    expansion: tuple[str, ...] = ()

    def describe(self) -> str:
        location = f"{self.filename}:{self.line}"
        if self.expansion:
            location += " (expanded from " + " -> ".join(self.expansion) + ")"
        return location


class AssemblyError(ValueError):
    """Invalid assembly with an optional source and macro-expansion location."""

    def __init__(self, message: str, source: SourceLine | None = None):
        self.message = message
        self.source = source
        super().__init__(f"{source.describe()}: {message}" if source else message)


@dataclass(frozen=True)
class _Macro:
    name: str
    parameters: tuple[str, ...]
    body: tuple[SourceLine, ...]
    source: SourceLine


@dataclass
class _Conditional:
    parent_active: bool
    condition: bool
    source: SourceLine
    directive: str
    seen_else: bool = False


def _without_comment(text: str, source: SourceLine) -> str:
    quote = None
    escaped = False
    for index, character in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in ('"', "'"):
            quote = character
        elif character == ";":
            return text[:index].strip()
    if quote:
        raise AssemblyError("unterminated quoted string", source)
    return text.strip()


def _split_arguments(text: str, source: SourceLine) -> list[str]:
    """Split comma-separated arguments without splitting expressions/strings."""
    if not text.strip():
        return []
    arguments = []
    start = 0
    depth = 0
    quote = None
    escaped = False
    for index, character in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in ('"', "'"):
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise AssemblyError("unmatched ')' in macro arguments", source)
        elif character == "," and depth == 0:
            arguments.append(text[start:index].strip())
            start = index + 1
    if depth or quote:
        raise AssemblyError("unclosed expression or string in macro arguments", source)
    arguments.append(text[start:].strip())
    if any(not argument for argument in arguments):
        raise AssemblyError("empty macro argument", source)
    return arguments


def _substitute(text: str, replacements: dict[str, str]) -> str:
    def substitute_token(match: re.Match) -> str:
        token = match.group()
        return replacements.get(token, token)

    return _TOKEN.sub(substitute_token, text)


class _Preprocessor:
    def __init__(self, include_dirs: Sequence[Path]):
        self.include_dirs = tuple(Path(directory) for directory in include_dirs)
        self.macros: dict[str, _Macro] = {}
        self.defined: set[str] = set()
        self.local_serial = 0
        self.output: list[SourceLine] = []
        self.include_stack: list[Path] = []
        self.constants: dict[str, int] = {}
        self.constant_definitions: set[str] = set()
        self.process_depth = 0

    @staticmethod
    def lines(source: str, filename: str, expansion: tuple[str, ...] = ()):
        result = []
        for number, text in enumerate(source.splitlines(), start=1):
            location = SourceLine(text, filename, number, expansion)
            result.append(replace(location, text=_without_comment(text, location)))
        return result

    def include(self, argument: str, source: SourceLine, macro_depth: int):
        match = re.fullmatch(r'"([^"\n]+)"', argument.strip())
        if not match:
            raise AssemblyError('.include requires one quoted filename', source)
        include_name = Path(match.group(1))
        base = Path(source.filename).parent if source.filename != "<string>" else Path.cwd()
        candidates = [base / include_name]
        candidates.extend(directory / include_name for directory in self.include_dirs)
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if path is None:
            raise AssemblyError(f"include file not found: {include_name}", source)
        if len(self.include_stack) >= 64:
            raise AssemblyError("include nesting exceeds 64 (possible include cycle)", source)
        path = path.resolve()
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            raise AssemblyError(f"cannot read include {path}: {error}", source) from error
        self.include_stack.append(path)
        try:
            self.process(self.lines(text, str(path), source.expansion), macro_depth)
        finally:
            self.include_stack.pop()

    @staticmethod
    def identifiers(argument: str, source: SourceLine, kind: str) -> tuple[str, ...]:
        names = tuple(_split_arguments(argument, source))
        if not names or any(not re.fullmatch(_IDENTIFIER, name) for name in names):
            raise AssemblyError(f"{kind} requires comma-separated identifiers", source)
        if len(names) != len(set(names)):
            raise AssemblyError(f"duplicate identifier in {kind}", source)
        return names

    def expand(self, macro: _Macro, argument: str, call: SourceLine, depth: int):
        if depth >= 64:
            raise AssemblyError("macro nesting exceeds 64 (possible recursion)", call)
        arguments = _split_arguments(argument, call)
        if len(arguments) != len(macro.parameters):
            raise AssemblyError(
                f"macro {macro.name} expects {len(macro.parameters)} argument(s), "
                f"got {len(arguments)}", call,
            )
        replacements = dict(zip(macro.parameters, arguments))
        self.local_serial += 1
        local_prefix = f"__asm_local_{self.local_serial}_"
        local_names: set[str] = set()
        for source in macro.body:
            directive = _DIRECTIVE.match(source.text)
            if directive and directive.group(1).lower() == ".local":
                names = self.identifiers(directive.group(2), source, ".local")
                for name in names:
                    if name in replacements or name in local_names:
                        raise AssemblyError(f"duplicate macro-local identifier: {name}", source)
                    replacements[name] = local_prefix + name
                    local_names.add(name)
        expansion = call.expansion + (f"{macro.name} at {call.filename}:{call.line}",)
        body = []
        for source in macro.body:
            directive = _DIRECTIVE.match(source.text)
            if directive and directive.group(1).lower() == ".local":
                continue
            body.append(replace(source, text=_substitute(source.text, replacements), expansion=expansion))
        self.process(body, depth + 1)

    def constant_value(self, expression: str, source: SourceLine, directive: str) -> int:
        try:
            return evaluate(expression, self.constants)
        except ExpressionError as error:
            raise AssemblyError(
                f"{directive} requires an already-defined constant expression: {error}",
                source,
            ) from error

    @staticmethod
    def repeat_lines(body: list[SourceLine], iterator: str | None,
                     iteration: int, frame: str) -> list[SourceLine]:
        """Substitute one lexical iterator, respecting nested iterator shadowing."""
        replacements = {iterator: str(iteration)} if iterator else {}
        result = []
        shadowed = False
        scopes = []
        for member in body:
            directive = _DIRECTIVE.match(member.text)
            name = directive.group(1).lower() if directive else None
            text = member.text
            if name == ".repeat":
                arguments = _split_arguments(directive.group(2), member)
                scopes.append(shadowed)
                if iterator and len(arguments) == 2 and arguments[1] == iterator:
                    # The nested count still belongs to the surrounding scope;
                    # its declared iterator and body belong to the inner one.
                    count = arguments[0] if shadowed else _substitute(arguments[0], replacements)
                    text = f".repeat {count}, {iterator}"
                    shadowed = True
                elif not shadowed:
                    text = _substitute(text, replacements)
            elif name == ".endrepeat":
                if scopes:
                    shadowed = scopes.pop()
            elif not shadowed:
                text = _substitute(text, replacements)
            result.append(replace(member, text=text, expansion=member.expansion + (frame,)))
        return result

    def process(self, lines: list[SourceLine], macro_depth: int = 0):
        if self.process_depth >= 128:
            raise AssemblyError("preprocessing nesting exceeds 128", lines[0] if lines else None)
        self.process_depth += 1
        try:
            self._process(lines, macro_depth)
        finally:
            self.process_depth -= 1

    def _process(self, lines: list[SourceLine], macro_depth: int):
        # Each include/macro/repeat owns balanced conditional nesting. A block
        # cannot accidentally close a conditional in its caller's source.
        guards: list[_Conditional] = []
        active = True
        index = 0
        while index < len(lines):
            source = lines[index]
            index += 1
            text = source.text
            if not text:
                continue
            directive = _DIRECTIVE.match(text)
            name = directive.group(1).lower() if directive else None
            argument = directive.group(2).strip() if directive else ""
            if name in (".if", ".ifndef"):
                if name == ".ifndef":
                    if not re.fullmatch(_IDENTIFIER, argument):
                        raise AssemblyError(".ifndef requires one identifier", source)
                    condition = argument not in self.defined if active else False
                else:
                    condition = bool(self.constant_value(argument, source, name)) if active else False
                guards.append(_Conditional(active, condition, source, name))
                active = active and condition
                continue
            if name == ".else":
                if argument:
                    raise AssemblyError("unexpected text after .else", source)
                if not guards:
                    raise AssemblyError(".else without .if/.ifndef", source)
                frame = guards[-1]
                if frame.seen_else:
                    raise AssemblyError("duplicate .else", source)
                frame.seen_else = True
                active = frame.parent_active and not frame.condition
                continue
            if name == ".endif":
                if argument:
                    raise AssemblyError("unexpected text after .endif", source)
                if not guards:
                    raise AssemblyError(".endif without .if/.ifndef", source)
                active = guards.pop().parent_active
                continue
            if name in (".ifdef", ".elseif"):
                raise AssemblyError(f"unsupported conditional directive: {name}", source)
            if name == ".repeat":
                # Collect before evaluating the count so an inactive block (or
                # count zero) never evaluates conditions in the repeated body.
                body = []
                nesting = 1
                while index < len(lines):
                    member = lines[index]
                    index += 1
                    member_directive = _DIRECTIVE.match(member.text)
                    member_name = member_directive.group(1).lower() if member_directive else None
                    if member_name == ".repeat":
                        nesting += 1
                    elif member_name == ".endrepeat":
                        nesting -= 1
                        if not nesting:
                            if member_directive.group(2).strip():
                                raise AssemblyError("unexpected text after .endrepeat", member)
                            break
                    body.append(member)
                else:
                    raise AssemblyError("unterminated .repeat", source)
                if active:
                    arguments = _split_arguments(argument, source)
                    if not 1 <= len(arguments) <= 2:
                        raise AssemblyError(".repeat requires count and optional iterator", source)
                    iterator = arguments[1] if len(arguments) == 2 else None
                    if iterator is not None and not re.fullmatch(_IDENTIFIER, iterator):
                        raise AssemblyError(".repeat iterator must be an identifier", source)
                    count = self.constant_value(arguments[0], source, name)
                    if not 0 <= count <= 65536:
                        raise AssemblyError(".repeat count must be in 0..65536", source)
                    for iteration in range(count):
                        frame = f"repeat {iteration} at {source.filename}:{source.line}"
                        expanded = self.repeat_lines(body, iterator, iteration, frame)
                        self.process(expanded, macro_depth)
                continue
            if name == ".endrepeat":
                raise AssemblyError(".endrepeat without .repeat", source)
            if name == ".macro":
                match = re.fullmatch(rf"({_IDENTIFIER})(?:\s+(.*))?", argument)
                if not match:
                    raise AssemblyError(".macro requires a name and optional parameters", source)
                body = []
                while index < len(lines):
                    member = lines[index]
                    index += 1
                    member_directive = _DIRECTIVE.match(member.text)
                    member_name = member_directive.group(1).lower() if member_directive else None
                    if member_name == ".macro":
                        raise AssemblyError("nested macro definitions are unsupported", member)
                    if member_name == ".endmacro":
                        if member_directive.group(2).strip():
                            raise AssemblyError("unexpected text after .endmacro", member)
                        break
                    body.append(member)
                else:
                    raise AssemblyError("unterminated .macro", source)
                if active:
                    macro_name = match.group(1)
                    if macro_name in self.macros:
                        raise AssemblyError(f"duplicate macro definition: {macro_name}", source)
                    parameters = self.identifiers(match.group(2), source, ".macro parameters") if match.group(2) else ()
                    self.macros[macro_name] = _Macro(macro_name, parameters, tuple(body), source)
                    self.defined.add(macro_name)
                continue
            if name == ".endmacro":
                raise AssemblyError(".endmacro without .macro", source)
            if not active:
                continue
            if name == ".local":
                raise AssemblyError(".local is only valid inside a macro", source)
            if name == ".include":
                self.include(argument, source, macro_depth)
                continue
            # Split labels from trailing macro calls (and instructions) without
            # changing their address. This also records labels for .ifndef.
            label = _LABEL.match(text)
            while label:
                self.defined.add(label.group(1))
                self.output.append(replace(source, text=label.group(1) + ":"))
                text = label.group(2).strip()
                label = _LABEL.match(text)
            if not text:
                continue
            source = replace(source, text=text)
            instruction = text.split(None, 1)
            macro = self.macros.get(instruction[0])
            if macro:
                self.expand(macro, instruction[1] if len(instruction) == 2 else "", source, macro_depth)
                continue
            assignment = _ASSIGNMENT.match(text)
            if assignment:
                constant = assignment.group(1)
                if constant in self.constant_definitions:
                    raise AssemblyError(f"duplicate symbol: {constant}", source)
                self.defined.add(constant)
                self.constant_definitions.add(constant)
                try:
                    self.constants[constant] = evaluate(text[assignment.end():], self.constants)
                except ExpressionError:
                    # Label/PC-dependent equates belong to layout. They remain
                    # unavailable to .if/.repeat instead of being guessed as 0.
                    pass
            self.output.append(source)
        if guards:
            frame = guards[-1]
            raise AssemblyError(f"unterminated {frame.directive}", frame.source)


def preprocess(
    source: str,
    *,
    filename: str = "<string>",
    include_dirs: Sequence[Path] = (),
) -> list[SourceLine]:
    """Expand supported includes/macros in an isolated preprocessing context."""
    frontend = _Preprocessor(include_dirs)
    frontend.process(frontend.lines(source, str(filename)))
    return frontend.output
