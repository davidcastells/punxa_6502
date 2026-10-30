"""Evaluate the integer expression subset used by the ISA assembly sources.

This is deliberately not Python expression evaluation.  Names are case-sensitive,
``$`` introduces hexadecimal integers, and ``*`` denotes the current byte PC.
Unary ``<`` and ``>`` extract the low and high byte; in infix position they are
comparisons.  Operators, from tightest to loosest, are unary ``+ - < >``, binary
``& ^`` (one shared level), ``+ -``, comparisons, and boolean ``.and``.  Parentheses override
precedence.  Unsupported ca65 syntax is rejected rather than approximated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re


class ExpressionError(ValueError):
    """An unsupported or malformed assembler expression."""


class UndefinedSymbolError(ExpressionError):
    """An expression references a symbol that is not yet defined."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"undefined symbol: {name}")


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    position: int


_TOKEN = re.compile(
    r"(?P<space>\s+)"
    r"|(?P<hex>\$[0-9a-fA-F]+)"
    r"|(?P<decimal>[0-9]+)"
    r"|(?P<identifier>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<dot_operator>\.[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<operator><>|<=|>=|[+\-&^<>=()*])"
)

_PRECEDENCE = {
    ".and": 10,
    "=": 20,
    "<>": 20,
    "<": 20,
    ">": 20,
    "<=": 20,
    ">=": 20,
    "^": 50,
    "&": 50,
    "+": 40,
    "-": 40,
}


def _tokenize(expression: str) -> list[_Token]:
    result = []
    position = 0
    while position < len(expression):
        match = _TOKEN.match(expression, position)
        if match is None:
            raise ExpressionError(
                f"unsupported character {expression[position]!r} "
                f"at column {position + 1}"
            )
        kind = match.lastgroup
        value = match.group()
        if kind != "space":
            if kind == "dot_operator":
                value = value.lower()
                if value != ".and":
                    raise ExpressionError(
                        f"unsupported operator {match.group()!r} "
                        f"at column {position + 1}"
                    )
                kind = "operator"
            result.append(_Token(kind, value, position))
        position = match.end()
    result.append(_Token("end", "", len(expression)))
    return result


class _Parser:
    def __init__(
        self, expression: str, symbols: Mapping[str, int], pc: int | None
    ) -> None:
        self.tokens = _tokenize(expression)
        self.index = 0
        self.symbols = symbols
        self.pc = pc

    @property
    def current(self) -> _Token:
        return self.tokens[self.index]

    def take(self) -> _Token:
        token = self.current
        self.index += 1
        return token

    def parse(self) -> int:
        if self.current.kind == "end":
            raise ExpressionError("empty expression")
        result = self.expression(0)
        if self.current.kind != "end":
            token = self.current
            raise ExpressionError(
                f"unexpected token {token.text!r} at column {token.position + 1}"
            )
        return result

    def expression(self, minimum: int) -> int:
        left = self.prefix()
        while self.current.text in _PRECEDENCE:
            operator = self.current.text
            precedence = _PRECEDENCE[operator]
            if precedence < minimum:
                break
            self.take()
            right = self.expression(precedence + 1)
            left = self.apply(operator, left, right)
        return left

    def prefix(self) -> int:
        token = self.current
        if token.kind == "end":
            raise ExpressionError("expected an operand at end of expression")
        self.take()
        if token.kind in {"decimal", "hex"}:
            try:
                return int(token.text[1:], 16) if token.kind == "hex" else int(token.text, 10)
            except ValueError as error:
                raise ExpressionError("integer literal is too large") from error
        if token.kind == "identifier":
            if token.text not in self.symbols:
                raise UndefinedSymbolError(token.text)
            value = self.symbols[token.text]
            if not isinstance(value, int):
                raise ExpressionError(f"symbol {token.text!r} is not an integer")
            return int(value)
        if token.text == "*":
            if self.pc is None:
                raise ExpressionError("current location '*' is not available")
            if not isinstance(self.pc, int):
                raise ExpressionError("current location must be an integer")
            return int(self.pc)
        if token.text == "(":
            value = self.expression(0)
            if self.current.text != ")":
                raise ExpressionError(
                    f"expected ')' at column {self.current.position + 1}"
                )
            self.take()
            return value
        if token.text in {"+", "-", "<", ">"}:
            value = self.expression(60)
            if token.text == "+":
                return value
            if token.text == "-":
                return -value
            if token.text == "<":
                return value & 0xFF
            return (value >> 8) & 0xFF
        raise ExpressionError(
            f"expected an operand, got {token.text!r} "
            f"at column {token.position + 1}"
        )

    @staticmethod
    def apply(operator: str, left: int, right: int) -> int:
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "&":
            return left & right
        if operator == "^":
            return left ^ right
        if operator == "=":
            return int(left == right)
        if operator == "<>":
            return int(left != right)
        if operator == "<":
            return int(left < right)
        if operator == ">":
            return int(left > right)
        if operator == "<=":
            return int(left <= right)
        if operator == ">=":
            return int(left >= right)
        if operator == ".and":
            return int(bool(left) and bool(right))
        raise ExpressionError(f"unsupported operator {operator!r}")


def evaluate(
    expression: str, symbols: Mapping[str, int], *, pc: int | None = None
) -> int:
    """Evaluate an integer expression without modifying the symbol mapping.

    Unresolved identifiers raise :class:`UndefinedSymbolError` so the assembly
    layout pass can defer forward references.  All operands are evaluated,
    including both sides of ``.and``; undefined symbols are never hidden by a
    false left operand.  Syntax outside the documented subset is an error.
    """
    if not isinstance(expression, str):
        raise ExpressionError("expression must be a string")
    try:
        return _Parser(expression, symbols, pc).parse()
    except RecursionError as error:
        raise ExpressionError("expression nesting is too deep") from error
