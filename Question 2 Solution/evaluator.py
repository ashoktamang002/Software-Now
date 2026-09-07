# ======================================================================================
#                              HIT137: SOFTWARE NOW
#                       Group Assignment 2: Question 2
# ======================================================================================
#                           Group Name: DAN/EXT 15
# ======================================================================================

#                               Group Members:
#                           -------------------------
#                           Ashok Tamang   -  S406128
#                           Rajesh Basnet  -  S404205
#                           Aryan Karki    -  S407507
#                           Ayun Neupane   -  S406923

# ======================================================================================
#                              PROGRAM DESCRIPTION
# ======================================================================================

# Running this file as a script (or calling "evaluate_file(input_path)" directly) will:
#
#  1. Read the input file, treating each line as one standalone arithmetic expression.
#  2. For every expression, in order:
#      a. Tokenize it into a flat list of typed tokens (numbers, operators, parentheses,
#         and a trailing end-of-input marker).
#      b. Parse those tokens into a nested parse tree via recursive descent.
#      c. Evaluate the tree to a single final numeric result.
#   3. Write "output.txt" to the same directory as the input file: one four-line block
#      per expression (Input / Tree / Tokens / Result), separated by a single blank line.
#   4. Return a list of dictionaries - one per expression, each with its input, tree,
#      tokens and result - so the same results can also be used programmatically.
#
# A line that fails at any stage does not stop the run: that stage (and every stage after
# it) is recorded as "ERROR" for that line only, and the next line is processed as normal.

# ----------------------------------------------------------------------------------------
# Grammar (lowest to highest precedence / binding)
# ----------------------------------------------------------------------------------------
#   Level 1:   + -                addition, subtraction                (left-associative)
#   Level 2:   * / % &            multiplication, division, modulo,    (left-associative)
#              Imp Mul            & implicit multiplication
#   Level 3:   unary-             negation                             (prefix)
#   Level 4:   ^                  exponentiation                       (right-associative)
#
# -----------------
# Numbers
# -----------------
# A number literal is one or more digits, optionally followed by a single "." and one
# or more further digits (e.g. "3", "3.5"). Negative numbers are never a single
# literal: a leading "-" is always its own OP token, folded in only by unary negation.
#
# -----------------
# Unary negation
# -----------------
# "-" may prefix a value at the start of an expression, immediately after "(", or
# immediately after any operator (e.g. "3 * -2", "-(3+4)"", "--5" is double negation).
# Unary "+" is explicitly not supported and is treated as an error if used.
#
# -------------------------
# Implicit multiplication
# -------------------------
# A value directly followed by "(" is treated as multiplication, e.g. "2(3+4)" behaves
# exactly like "2*(3+4)". Two adjacent number literals with nothing between them (e.g.
# "2 3") are NOT implicit multiplication - that combination is invalid syntax and is
# reported as an error rather than silently multiplied.
#
# -----------------
# Output format
# -----------------
# Each expression produces a four-line block in "output.txt":
#   Input  -> the original expression exactly as read from the file.
#   Tree   -> the parse tree, or "ERROR". A number shows as its formatted value; a binary
#             operation shows as "(op left right)"; a unary negation shows as
#             "(neg operand)"; implicit multiplication appears in the tree as "*".
#   Tokens -> each token as "[TYPE:value]" separated by single spaces, ending with
#             "[END]", or "ERROR". Token types are NUM, OP, LPAREN, RPAREN and END.
#   Result -> the computed value, or "ERROR". A whole-number result (e.g. 8.0) is shown
#             with no decimal point (e.g. 8); any other result is rounded to 4 decimals.
# Blocks for successive expressions are separated by exactly one blank line.
#
# -----------------
# Errors
# -----------------
# Invalid characters, malformed numbers (e.g. a "." with no following digit), unbalanced
# or mismatched parentheses, unsupported unary "+", and any other invalid syntax are all
# caught during tokenising or parsing and reported as "ERROR" instead of crashing the
# program. Division/modulo by zero, and exponentiation that produces a complex result
# (e.g. a negative base with a fractional exponent), are caught separately at the
# evaluation stage -- in these cases the Tree and Tokens lines still display normally,
# and only the Result line reads "ERROR".

# ======================================================================================
#                              SOLUTION START
# ======================================================================================

from __future__ import annotations # Enable postponed evaluation of annotations
from typing import Any             # Import the "Any" type for flexible type annotations
import os                          # Import OS functions

# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

Token = tuple[str, str]

def tokenize(expression: str) -> list[Token]:
    """
    Convert a mathematical expression into a list of tokens.

    It reads the expression character by character, identifies spaces,
    operators, parentheses, and numbers, and stores each item as a token.
    Numbers can contain a decimal point. An END token is added at the end
    to indicate that the entire expression has been processed.
    """
    tokens: list[Token] = []
    i = 0
    length = len(expression)

    while i < length:
        char = expression[i]

        if char == ' ' or char == '\t':       # skip spaces and tabs
            i += 1

        elif char in '+-*/%^':                # any operator symbol
            tokens.append(("OP", char))
            i += 1

        elif char == '(':
            tokens.append(("LPAREN", "("))
            i += 1

        elif char == ')':
            tokens.append(("RPAREN", ")"))
            i += 1

        elif char.isdigit():                  # read a whole number literal
            start = i
            while i < length and expression[i].isdigit():
                i += 1

            # a number may have a single dot followed by one or more digits
            if i < length and expression[i] == '.':
                i += 1
                if i >= length or not expression[i].isdigit():
                    raise ValueError("a number needs digits after the '.'")
                while i < length and expression[i].isdigit():
                    i += 1
            tokens.append(("NUM", expression[start:i]))

        else:                                               # anything else is not allowed
            raise ValueError("invalid character: " + char)

    tokens.append(("END", ""))                              # sentinel token so the parser can detect end-of-input
    return tokens

def format_tokens(tokens: list[Token]) -> str:
    """
    Convert the list of tokens into a readable string.

    It goes through each token, formats it according to its type and value,
    and joins all formatted tokens together with spaces. The END token is
    displayed as [END].
    """
    parts: list[str] = []
    for ttype, tvalue in tokens:
        if ttype == 'END':
            parts.append('[END]')
        else:
            parts.append(f'[{ttype}:{tvalue}]')
    return ' '.join(parts)  # single spaces between tokens, as required by the spec

# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------

def parse(tokens: list[Token]) -> Any:
    """
    Convert a list of tokens into a parse tree representing the expression.

    It uses recursive-descent parsing with several levels of functions to
    handle operator precedence. It processes addition/subtraction,
    multiplication/division/modulo, unary minus, powers, numbers, and
    parentheses. It also checks that no unexpected tokens remain.
    """
    pos = 0 # shared cursor into 'tokens'; moved forward only by advance()/expect()

    def peek() -> Token:
        """Look at the current token without moving to the next token."""
        return tokens[pos]

    def advance() -> Token:
        """
        Return the current token and move to the next token.

        It uses the nonlocal position variable so that the parser can keep
        track of which token it is currently processing.
        """
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        return tok

    def expect(token_type: str) -> Token:
        """
        Check that the current token has the expected type.

        If the token type is correct, it advances to the next token and
        returns the current token. Otherwise, it raises a ValueError.
        """
        nonlocal pos
        tok = tokens[pos]
        if tok[0] != token_type:
            raise ValueError(f"Expected {token_type} but found {tok[0]}")
        pos += 1
        return tok

    # Level 1: + - (left associative)
    def parse_expression() -> Any:
        """
        Parse addition and subtraction expressions.

        It first parses a term and then repeatedly looks for '+' or '-'.
        Each operation is added to the parse tree from left to right,
        making these operators left-associative.
        """
        node = parse_term()
        # keep folding left as long as another + or - follows, building a left-associative chain
        while peek()[0] == 'OP' and peek()[1] in ('+', '-'):
            op = advance()[1]
            right = parse_term()
            node = ('binop', op, node, right)
        return node

    # Level 2: * / % and implicit multiplication (left associative)
    def parse_term() -> Any:
        """
        Parse multiplication, division, modulo, and implicit multiplication.

        It first parses a unary expression and then repeatedly checks for
        '*', '/', '%', or a parenthesis immediately following a factor.
        When a parenthesis follows a factor, implicit multiplication is
        represented as a '*' operation in the parse tree.
        """
        node = parse_unary()
        while True:
            tok = peek()
            if tok[0] == 'OP' and tok[1] in ('*', '/', '%'):
                op = advance()[1]
                right = parse_unary()
                node = ('binop', op, node, right)
            elif tok[0] == 'LPAREN':
                # Implicit multiplication: a factor directly followed by '('
                right = parse_unary()
                node = ('binop', '*', node, right)
            else:
                break
        return node

    # Level 3: unary minus (prefix). Unary '+' is explicitly unsupported.
    def parse_unary() -> Any:
        """
        Parse unary minus and reject unary plus.

        If the current token is '-', it advances past it, recursively parses
        the following expression, and creates a 'neg' node. Unary '+' is
        rejected with a ValueError. Otherwise, it continues to parse a power.
        """
        tok = peek()
        if tok[0] == 'OP' and tok[1] == '-':
            advance()                           # consume the '-'
            operand = parse_unary()             # recurse so chained signs like "--5" both apply
            return ('neg', operand)
        if tok[0] == 'OP' and tok[1] == '+':
            raise ValueError("Unary '+' is not supported")  # explicitly disallowed by the spec
        return parse_power()

    # Level 4: ^ (right associative; exponent may itself carry a unary '-')
    def parse_power() -> Any:
        """
        Parse exponentiation using the '^' operator.

        It first parses the base and then checks for '^'. If '^' is found,
        it parses the exponent and creates a binary-operation node.
        """
        base = parse_primary()
        tok = peek()
        if tok[0] == 'OP' and tok[1] == '^':
            advance()
            # the exponent is parsed via parse_unary(), not parse_power(): this lets the
            # exponent itself start with a '-', and makes chained '^' chains right-associative
            exponent = parse_unary()
            return ('binop', '^', base, exponent)
        return base

    # Numbers and parenthesised sub-expressions
    def parse_primary() -> Any:
        """
        Parse a number or a parenthesised expression.

        A number is converted from text to a float and stored as a 'num'
        node. If an opening parenthesis is found, the function parses the
        expression inside it and checks for the matching closing parenthesis.
        """
        tok = peek()
        if tok[0] == 'NUM':
            advance()
            return ('num', float(tok[1]))           # numeric literals are stored as floats
        if tok[0] == 'LPAREN':
            advance()                               # consume '('
            node = parse_expression()               # recurse to the top of the grammar for the inside
            expect('RPAREN')                        # the matching ')' is mandatory
            return node
        raise ValueError(f"Unexpected token {tok[0]}")  # nothing else can start a primary

    tree = parse_expression()                       # parse the whole expression from the top of the grammar
    if peek()[0] != 'END':
        # leftover tokens (e.g. a stray ')') mean the expression wasn't fully consumed
        raise ValueError(f"Unexpected trailing token {peek()[0]}")
    return tree

# ---------------------------------------------------------------------------
# Tree formatting, evaluation and result formatting
# ---------------------------------------------------------------------------

def format_number(value: float) -> str:
    """
    Convert a numeric value into a readable string.

    It first converts the value to a float. If the value is a whole number,
    it removes the unnecessary decimal part. Otherwise, it rounds the value
    to four decimal places.
    """
    value = float(value)                # normalise in case an int was passed in
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))        # whole numbers display with no decimal point
    return str(rounded)                 # otherwise the 4-decimal rounded value

def format_tree(node: Any) -> str:
    """
    Convert a parse tree into a readable tree representation.

    It checks the type of each node and recursively formats its child nodes.
    Number nodes, unary negation nodes, and binary-operation nodes are each
    converted into a corresponding text representation.
    """
    node_type = node[0]

    # Number literal
    if node_type == 'num':
        return format_number(node[1])

    # Unary negation
    if node_type == 'neg':
        operand = format_tree(node[1])
        return f"(neg {operand})"

    # Binary operation
    if node_type == 'binop':
        operator = node[1]
        left = format_tree(node[2])
        right = format_tree(node[3])

        return f"({operator} {left} {right})"

    # Invalid/unknown tree node
    raise ValueError("Invalid parse tree node")

def build_parse_tree(tokens: list[Token]) -> str:
    """
    Build and format a parse tree from a list of tokens.

    It first sends the tokens to parse() to create the parse tree and then
    sends the resulting tree to format_tree() to produce a readable string.
    """
    tree = parse(tokens)        # build the nested tuple tree
    return format_tree(tree)    # render it as a fully-parenthesised string

def tokens_to_str(tokens: list[Token]) -> str:
    """
    Convert tokens into a readable string representation.

    It loops through each token and formats its type and value. The END
    token is displayed separately as [END].
    """
    parts: list[str] = []
    for t_type, value in tokens:
        parts.append("[END]" if t_type == "END" else f"[{t_type}:{value}]")
    return " ".join(parts) # functionally the same as format_tokens(); this is the version evaluate_file() actually calls

def eval_tree(node: Any) -> float:
    """
    Evaluate a parse tree and return the calculated numeric result.

    It recursively evaluates child nodes and then performs the operation
    stored in each binary-operation node. It also handles unary negation,
    checks for division or modulo by zero, and rejects complex power results.
    """
    kind = node[0]
    if kind == 'num':
        return node[1]                           # a number node stores its float value directly
    if kind == 'neg':
        return -eval_tree(node[1])               # evaluate the operand first, then negate it
    if kind == 'binop':
        _, op, left, right = node
        l, r = eval_tree(left), eval_tree(right) # evaluate both sides before combining them
        if op == '+': return l + r
        if op == '-': return l - r
        if op == '*': return l * r
        if op == '/':
            if r == 0:
                raise ZeroDivisionError("division by zero")     # guard before dividing
            return l / r
        if op == '%':
            if r == 0:
                raise ZeroDivisionError("division by zero")     # guard before taking the modulo
            return l % r
        if op == '^':
            result = l ** r
            # a negative base with a fractional exponent produces a complex number in Python;
            # this evaluator only deals in real numbers, so treat that case as an error
            if isinstance(result, complex):
                raise ValueError("complex result")
            return result
    raise ValueError("unknown node type")   # should be unreachable for a well-formed tree

def format_result(value: float) -> str:
    """
    Convert the final calculation result into a readable string.

    Whole numbers are displayed without a decimal part, while other values
    are rounded to four decimal places.
    """
    rounded = round(value, 4)
    if rounded == int(rounded):
        return str(int(rounded))        # whole numbers display with no decimal point
    return str(rounded)                 # otherwise the 4-decimal rounded value

# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def _format_block(entry: dict[str, Any]) -> str:
    """
    Format one expression's input, tree, tokens, and result into a text block.

    It retrieves the relevant values from the entry dictionary and combines
    them into a structured multi-line string for the output file.
    """
    # line order matches the required output format: Input, Tree, Tokens, Result
    return (f"Input: {entry['input']}\n"
            f"Tree: {entry['tree']}\n"
            f"Tokens: {entry['tokens']}\n"
            f"Result: {entry['result_str']}")

def evaluate_file(input_path: str) -> list[dict[str, Any]]:
    """
    Read, process, evaluate, and save the results for all expressions in a file.

    It reads each expression, tokenises it, parses the tokens into a tree,
    evaluates the tree, formats the results, and handles errors at each stage.
    Finally, it writes all results to output.txt and returns the processed
    results as a list of dictionaries.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()   # one line = one expression to evaluate

    results: list[dict[str, Any]] = []
    blocks: list[str] = []

    for expr in lines:
        # start each entry assuming failure; fields are overwritten as each stage succeeds
        entry: dict[str, Any] = {"input": expr, "tree": None, "tokens": None,
                  "result": "ERROR", "result_str": "ERROR"}

        # --- Stage 1: tokenize ---------------------------------------------------
        try:
            tokens = tokenize(expr)
            entry["tokens"] = tokens_to_str(tokens)
        except ValueError:
            # tokenizing failed, so there's no valid token list to parse either
            entry["tokens"] = "ERROR"
            entry["tree"] = "ERROR"
            results.append(entry); blocks.append(_format_block(entry))
            continue    # skip stages 2-3, move on to the next line

        # --- Stage 2: parse -------------------------------------------------------
        try:
            tree = parse(tokens)
            entry["tree"] = format_tree(tree)  
        except ValueError:
            # tokens were valid but the syntax wasn't; keep the good tokens, mark the tree
            entry["tree"] = "ERROR"
            results.append(entry); blocks.append(_format_block(entry))
            continue    # skip stage 3, move on to the next line

        # --- Stage 3: evaluate ------------------------------------------------------
        try:
            value = eval_tree(tree)
            entry["result"] = value
            entry["result_str"] = format_result(value)
        except (ZeroDivisionError, ValueError, OverflowError):
            # tokens and tree were valid; only the arithmetic itself failed
            # (e.g. divide by zero, or a complex result from exponentiation)
            entry["result"] = "ERROR"
            entry["result_str"] = "ERROR"

        results.append(entry); blocks.append(_format_block(entry))

    # write one four-line block per expression, separated by a blank line, beside the input file
    out_dir = os.path.dirname(input_path) or "."    # fall back to cwd if input_path has no folder
    with open(os.path.join(out_dir, "output.txt"), 'w', encoding='utf-8') as f:
        f.write("\n\n".join(blocks)+ "\n")

    # "result_str" is only needed for the text report; drop it before returning to the caller
    return [{"input": e["input"], "tree": e["tree"], "tokens": e["tokens"], "result": e["result"]}
            for e in results]

if __name__ == "__main__":
    evaluate_file("input.txt")     # Entry point: run evaluate_file() only when this script is executed directly