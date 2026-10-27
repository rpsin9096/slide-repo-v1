"""FocusGate v3.0 — Static AST Loop Safety Analyzer.

Statically analyzes Python AST for infinite loop patterns, unhalting while loops,
unmodified loop condition variables, and unbounded recursive cycles.

100% Python stdlib, zero external dependencies.
"""

import ast
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional


@dataclass
class LoopIssue:
    """A detected loop termination or safety defect."""
    issue_type: str
    line_number: int
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "line_number": self.line_number,
            "description": self.description
        }


@dataclass
class LoopSafetyReport:
    """Comprehensive safety assessment of analyzed source code."""
    is_safe: bool
    issues: List[LoopIssue]
    checked_loops: int
    checked_functions: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "issues": [i.to_dict() for i in self.issues],
            "checked_loops": self.checked_loops,
            "checked_functions": self.checked_functions
        }


class ASTLoopAnalyzer:
    """Performs static flow and AST inspection for loop non-termination hazards."""

    def analyze_code(self, code: str, filename: str = "<string>") -> LoopSafetyReport:
        """Parses and audits code string for unhalting loop hazards."""
        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError as e:
            return LoopSafetyReport(
                is_safe=False,
                issues=[LoopIssue("SYNTAX_ERROR", e.lineno or 1, f"Syntax error: {e.msg}")],
                checked_loops=0,
                checked_functions=0
            )

        issues: List[LoopIssue] = []
        checked_loops = 0
        checked_functions = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                checked_loops += 1
                self._check_while_loop(node, issues)
            elif isinstance(node, ast.FunctionDef):
                checked_functions += 1
                self._check_function_recursion(node, issues)

        lines = code.splitlines()
        filtered_issues = []
        for iss in issues:
            if 1 <= iss.line_number <= len(lines):
                line_str = lines[iss.line_number - 1]
                if "pragma: no-loop-check" in line_str or "noqa" in line_str:
                    continue
            filtered_issues.append(iss)

        return LoopSafetyReport(
            is_safe=(len(filtered_issues) == 0),
            issues=filtered_issues,
            checked_loops=checked_loops,
            checked_functions=checked_functions
        )

    def _has_terminator(self, nodes: List[ast.stmt]) -> bool:
        """Checks if statement list contains a break, return, or raise."""
        for child in ast.walk(ast.Module(body=nodes, type_ignores=[])):
            if isinstance(child, (ast.Break, ast.Return, ast.Raise)):
                return True
        return False

    def _has_side_effect_call(self, nodes: List[ast.stmt]) -> bool:
        """Checks if statement list contains any function or method call."""
        for child in ast.walk(ast.Module(body=nodes, type_ignores=[])):
            if isinstance(child, ast.Call):
                return True
        return False

    def _is_constant_truthy(self, test_node: ast.AST) -> bool:
        """Checks if a condition expression evaluates to constant Truth."""
        # `ast.NameConstant` was an alias for `ast.Constant` from 3.8 and was
        # REMOVED in 3.12. v3.1 documents "Python 3.9+", so the second branch
        # worked on 3.9-3.11 and raised
        # `AttributeError: module 'ast' has no attribute 'NameConstant'`
        # on 3.12+ -- the whole analyzer crashed on any while-loop it
        # inspected. Found in v3.2 Loop 64: a suite run under a 3.14
        # interpreter failed here while 4 runs under 3.9.6 were green.
        # `ast.Constant` covers True/False/None on every supported version,
        # so the first branch already does the whole job and the alias is
        # simply gone.
        if isinstance(test_node, ast.Constant):
            return bool(test_node.value)
        return False

    def _get_variables_in_expr(self, expr: ast.AST) -> Set[str]:
        """Extracts local variable names referenced in an expression."""
        names = set()
        for node in ast.walk(expr):
            if isinstance(node, ast.Name):
                if node.id not in ("self", "cls", "True", "False", "None"):
                    names.add(node.id)
        return names

    def _modifies_variable(self, nodes: List[ast.stmt], var_names: Set[str]) -> bool:
        """Checks if any statement in nodes modifies any of var_names."""
        for node in ast.walk(ast.Module(body=nodes, type_ignores=[])):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in var_names:
                        return True
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name) and node.target.id in var_names:
                    return True
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id in var_names:
                    return True
        return False

    def _check_while_loop(self, node: ast.While, issues: List[LoopIssue]) -> None:
        """Audits while-loop for infinite termination hazard."""
        has_term = self._has_terminator(node.body)

        # 1. While True / Constant Truth
        if self._is_constant_truthy(node.test):
            if not has_term:
                issues.append(LoopIssue(
                    issue_type="INFINITE_WHILE_TRUE",
                    line_number=node.lineno,
                    description=f"While-loop on line {node.lineno} has constant truth condition with no break, return, or raise."
                ))
            return

        # 2. Dynamic Condition: check variable modifications
        cond_vars = self._get_variables_in_expr(node.test)
        if cond_vars:
            # If the loop doesn't terminate and doesn't modify condition variables, and has no side-effect calls
            if not has_term and not self._modifies_variable(node.body, cond_vars) and not self._has_side_effect_call(node.body):
                issues.append(LoopIssue(
                    issue_type="UNMODIFIED_LOOP_CONDITION",
                    line_number=node.lineno,
                    description=f"While-loop on line {node.lineno} condition relies on {cond_vars} which are never modified in body."
                ))

    def _check_function_recursion(self, node: ast.FunctionDef, issues: List[LoopIssue]) -> None:
        """Checks for unguarded recursive self-calls."""
        fn_name = node.name
        is_method = bool(node.args.args and node.args.args[0].arg in ("self", "cls"))

        for stmt in node.body:
            for call in ast.walk(stmt):
                if isinstance(call, ast.Call):
                    is_recursive_call = False
                    if not is_method and isinstance(call.func, ast.Name) and call.func.id == fn_name:
                        is_recursive_call = True
                    elif is_method and isinstance(call.func, ast.Attribute) and call.func.attr == fn_name:
                        if isinstance(call.func.value, ast.Name) and call.func.value.id in ("self", "cls"):
                            is_recursive_call = True

                    if is_recursive_call:
                        is_guarded = any(isinstance(p, ast.If) for p in ast.walk(node) if call in ast.walk(p))
                        if not is_guarded:
                            issues.append(LoopIssue(
                                issue_type="UNBOUNDED_RECURSION",
                                line_number=node.lineno,
                                description=f"Function '{fn_name}' on line {node.lineno} contains unguarded recursive call."
                            ))
                            return
