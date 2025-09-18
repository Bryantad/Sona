"""
Sona Language Interpreter v0.9.0 - Documentation-Aligned Implementation

This interpreter implements the exact syntax shown in the Sona documentation and wiki book.
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lark import Lark, Token, Transformer, Tree


class SonaDocumentedInterpreter(Transformer): """Interpreter that matches the documented Sona syntax"""

    def __init__(self): self.variables = {}
        self.functions = {}
        self.output_buffer = []

    def execute(self, code: str): """Execute Sona code using the documented syntax"""
        try: # Load the documented grammar
            grammar_path = Path(__file__).parent / "grammar_documented.lark"
            with open(grammar_path, 'r') as f: grammar = f.read()

            parser = Lark(grammar, start = 'start', parser = 'lalr')
            tree = parser.parse(code)

            # Clear output buffer
            self.output_buffer = []

            # Transform the tree
            result = self.transform(tree)

            return self.output_buffer

        except Exception as e: return [f"Error: {str(e)}"]

    def start(self, statements): """Process all statements"""
        result = None
        for stmt in statements: if stmt is not None: result = stmt
        return result

    # = (
        ======= Cognitive Accessibility Statements ======== def think_stmt(self, args): """Handle think statements - these are cognitive comments"""
    )
        message = args[0]
        # Think statements are cognitive aids - they don't produce output
        # but could be used for debugging or cognitive assistance
        return f"💭 {message}"

    def show_stmt(self, args): """Handle show statements - these are output statements"""
        value = args[0]
        output = str(value)
        self.output_buffer.append(output)
        return output

    def calculate_assign(self, args): """Handle calculate statements - these are assignments with cognitive clarity"""
        name = args[0]
        value = args[1]
        self.variables[name] = value
        return value

    # = (
        ======= Loop Statements ======== def repeat_times(self, args): """Handle repeat N times loops"""
    )
        times = int(args[0])
        block = args[1]

        for i in range(times): for stmt in block: if stmt is not None: self.transform(stmt)
        return None

    def repeat_for_each(self, args): """Handle repeat for each item in list loops"""
        var_name = str(args[0])
        iterable = args[1]
        block = args[2]

        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)

        try: if isinstance(iterable, list): for item in iterable: self.variables[var_name] = (
            item
        )
                    for stmt in block: if stmt is not None: result = (
                        self.transform(stmt)
                    )
            else: # Handle single item
                self.variables[var_name] = iterable
                for stmt in block: if stmt is not None: result = (
                    self.transform(stmt)
                )
        finally: # Restore old value
            if old_value is not None: self.variables[var_name] = old_value
            elif var_name in self.variables: del self.variables[var_name]

        return None

    def repeat_for_range(self, args): """Handle repeat for i from start to end loops"""
        var_name = args[0]
        start = int(args[1])
        end = int(args[2])
        block = args[3]

        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)

        try: for i in range(start, end + 1): self.variables[var_name] = i
                for stmt in block: if stmt is not None: self.transform(stmt)
        finally: # Restore old value
            if old_value is not None: self.variables[var_name] = old_value
            elif var_name in self.variables: del self.variables[var_name]

        return None

    def repeat_for_range_step(self, args): """Handle repeat for i from start to end step N loops"""
        var_name = args[0]
        start = int(args[1])
        end = int(args[2])
        step = int(args[3])
        block = args[4]

        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)

        try: for i in range(start, end + 1, step): self.variables[var_name] = i
                for stmt in block: if stmt is not None: self.transform(stmt)
        finally: # Restore old value
            if old_value is not None: self.variables[var_name] = old_value
            elif var_name in self.variables: del self.variables[var_name]

        return None

    # = (
        ======= Conditional Statements ======== def when_stmt(self, args): """Handle when statements - cognitive-friendly conditionals"""
    )
        condition = args[0]
        then_block = args[1]
        else_block = args[2] if len(args) > 2 else None

        if condition: for stmt in then_block: if stmt is not None: self.transform(stmt)
        elif else_block: for stmt in else_block: if stmt is not None: self.transform(stmt)

        return None

    def if_stmt(self, args): """Handle traditional if statements"""
        condition = args[0]
        then_stmts = args[1]
        else_stmts = args[2] if len(args) > 2 else []

        if condition: for stmt in then_stmts: if stmt is not None: self.transform(stmt)
        else: for stmt in else_stmts: if stmt is not None: self.transform(stmt)

        return None

    # = (
        ======= Traditional Statements ======== def while_stmt(self, args): """Handle while loops"""
    )
        condition_tree = args[0]
        statements = args[1]

        while True: condition = self.transform(condition_tree)
            if not condition: break

            for stmt in statements: if stmt is not None: self.transform(stmt)

        return None

    def for_stmt(self, args): """Handle for loops"""
        var_name = args[0]
        iterable = args[1]
        statements = args[2]

        # Save current value of loop variable if it exists
        old_value = self.variables.get(var_name)

        try: for item in iterable: self.variables[var_name] = item
                for stmt in statements: if stmt is not None: self.transform(stmt)
        finally: # Restore old value
            if old_value is not None: self.variables[var_name] = old_value
            elif var_name in self.variables: del self.variables[var_name]

        return None

    # = (
        ======= Function Definition ======== def func_def(self, args): """Handle function definitions"""
    )
        name = args[0]
        params = args[1] if len(args) > 2 else []
        body = args[-1]

        self.functions[name] = {'params': params, 'body': body}

        return None

    def func_call(self, args): """Handle function calls"""
        name = args[0]
        call_args = args[1:] if len(args) > 1 else []

        if name in self.functions: func = self.functions[name]

            # Save current variables
            old_vars = self.variables.copy()

            # Set parameters
            for i, param in enumerate(func['params']): if i < len(call_args): self.variables[param] = (
                call_args[i]
            )

            try: # Execute function body
                for stmt in func['body']: if stmt is not None: self.transform(stmt)

                return None
            finally: # Restore variables
                self.variables = old_vars

        return None

    # = (
        ======= Expressions ======== def add(self, args): return args[0] + args[1]
    )

    def sub(self, args): return args[0] - args[1]

    def mul(self, args): return args[0] * args[1]

    def div(self, args): return args[0] / args[1]

    def eq(self, args): return args[0] == args[1]

    def neq(self, args): return args[0] != args[1]

    def gt(self, args): return args[0] > args[1]

    def lt(self, args): return args[0] < args[1]

    def gte(self, args): return args[0] >= args[1]

    def lte(self, args): return args[0] <= args[1]

    def and_op(self, args): return args[0] and args[1]

    def or_op(self, args): return args[0] or args[1]

    def neg(self, args): return -args[0]

    def not_op(self, args): return not args[0]

    # = (
        ======= Atomic expressions ======== def number(self, args): token = args[0]
    )
        if '.' in token: return float(token)
        return int(token)

    def string(self, args): token = args[0]
        # Remove quotes
        return token[1:-1]

    def true(self, args): return True

    def false(self, args): return False

    def var(self, args): name = args[0]
        if name in self.variables: return self.variables[name]
        raise NameError(f"Undefined variable: {name}")

    def var_assign(self, args): name = args[0]
        value = args[1]
        self.variables[name] = value
        return value

    def array(self, args): return list(args)

    def dict(self, args): result = {}
        for i in range(0, len(args), 2): key = args[i]
            value = args[i + 1]
            result[key] = value
        return result

    def index_access(self, args): obj = args[0]
        index = args[1]
        return obj[index]

    def property_access(self, args): obj = args[0]
        prop = args[1]
        if isinstance(obj, dict): return obj.get(prop)
        return getattr(obj, prop, None)

    # = (
        ======= Helper methods ======== def block(self, args): """Handle block statements"""
    )
        return args

    def param_list(self, args): """Handle parameter lists"""
        return args

    def args(self, args): """Handle argument lists"""
        return args
