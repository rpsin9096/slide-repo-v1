"""FocusGate v3.1 Loop 55 — Full Workspace Anti-Cliché & Infinite Loop Safety Guardian.

Exhaustive static AST and dynamic safety analyzer detecting unbounded while loops,
unhalted recursion, and sleep-less polling to prevent runaway CPU starvation.

Zero external dependencies (100% Python stdlib).
"""

import os
import ast
from typing import List, Dict, Any, Optional, Set


class _LoopSafetyTransformer(ast.NodeTransformer):
    """AST transformer that injects safety counter guards into unbounded while loops."""

    def __init__(self) -> None:
        super().__init__()
        self.guard_id = 0

    def _is_unbounded_while(self, node: ast.While) -> bool:
        # Check if condition is a constant truthy value
        is_const_true = False
        if isinstance(node.test, ast.Constant) and bool(node.test.value) is True:
            is_const_true = True
        elif isinstance(node.test, ast.Name) and node.test.id == "True":
            is_const_true = True

        if not is_const_true:
            return False

        # Look for break, return, raise, or sleep in body
        for child in ast.walk(node):
            if isinstance(child, (ast.Break, ast.Return, ast.Raise)):
                return False
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name) and func.id == "sleep":
                    return False
                if isinstance(func, ast.Attribute) and func.attr == "sleep":
                    return False

        return True

    def _transform_body_list(self, statements: List[ast.stmt]) -> List[ast.stmt]:
        new_stmts: List[ast.stmt] = []
        for stmt in statements:
            if isinstance(stmt, ast.While) and self._is_unbounded_while(stmt):
                self.guard_id += 1
                var_name = f"_loop_guard_counter_{self.guard_id}"

                # Create: _loop_guard_counter_N = 0
                init_stmt = ast.Assign(
                    targets=[ast.Name(id=var_name, ctx=ast.Store())],
                    value=ast.Constant(value=0),
                )
                new_stmts.append(init_stmt)

                # Inside while body:
                # _loop_guard_counter_N += 1
                inc_stmt = ast.AugAssign(
                    target=ast.Name(id=var_name, ctx=ast.Store()),
                    op=ast.Add(),
                    value=ast.Constant(value=1),
                )

                # if _loop_guard_counter_N > 100000: break
                break_cond = ast.If(
                    test=ast.Compare(
                        left=ast.Name(id=var_name, ctx=ast.Load()),
                        ops=[ast.Gt()],
                        comparators=[ast.Constant(value=100000)],
                    ),
                    body=[ast.Break()],
                    orelse=[],
                )

                stmt.body = [inc_stmt, break_cond] + stmt.body
                new_stmts.append(stmt)
            else:
                new_stmts.append(stmt)

        return new_stmts

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._transform_body_list(node.body)
        return node

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)
        node.body = self._transform_body_list(node.body)
        return node


class InfiniteLoopGuardian:
    """Audits and remediates Python ASTs to guard against runaway CPU and infinite loops."""

    def audit_source(self, code: str, filename: str = "<memory>") -> List[Dict[str, Any]]:
        """Audits Python source code string for infinite loop hazards and unbounded recursion."""
        issues: List[Dict[str, Any]] = []

        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError as e:
            return [{
                "category": "SYNTAX_ERROR",
                "severity": "HIGH",
                "filename": filename,
                "line": e.lineno or 1,
                "message": f"Syntax error: {e.msg}",
            }]

        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                self._check_while_loop(node, filename, issues)
            elif isinstance(node, ast.FunctionDef):
                self._check_recursion(node, filename, issues)

        return issues

    def _check_while_loop(self, node: ast.While, filename: str, issues: List[Dict[str, Any]]) -> None:
        is_const_true = False
        if isinstance(node.test, ast.Constant) and bool(node.test.value) is True:
            is_const_true = True
        elif isinstance(node.test, ast.Name) and node.test.id == "True":
            is_const_true = True

        if not is_const_true:
            return

        has_break = False
        has_return = False
        has_raise = False
        has_sleep = False
        has_checkpoint = False

        for child in ast.walk(node):
            if isinstance(child, ast.Break):
                has_break = True
            elif isinstance(child, ast.Return):
                has_return = True
            elif isinstance(child, ast.Raise):
                has_raise = True
            elif isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name):
                    if func.id == "sleep":
                        has_sleep = True
                    elif func.id == "checkpoint":
                        has_checkpoint = True
                elif isinstance(func, ast.Attribute):
                    if func.attr == "sleep":
                        has_sleep = True
                    elif func.attr == "checkpoint":
                        has_checkpoint = True

        if not (has_break or has_return or has_raise or has_sleep or has_checkpoint):
            issues.append({
                "category": "UNBOUNDED_WHILE_LOOP",
                "severity": "CRITICAL",
                "filename": filename,
                "line": getattr(node, "lineno", 1),
                "message": "Unbounded while loop detected without break, return, raise, sleep, or checkpoint.",
            })

    def _check_recursion(self, node: ast.FunctionDef, filename: str, issues: List[Dict[str, Any]]) -> None:
        fn_name = node.name
        recursive_calls: List[ast.Call] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == fn_name:
                    recursive_calls.append(child)

        if not recursive_calls:
            return

        # Check if there is an explicit base case guard returning or raising
        has_base_case_guard = False
        for child in node.body:
            if isinstance(child, ast.If):
                for sub in ast.walk(child):
                    if isinstance(sub, (ast.Return, ast.Raise)):
                        has_base_case_guard = True
                        break
            if has_base_case_guard:
                break

        if has_base_case_guard:
            return

        # Check if all recursive calls are conditionally guarded within If blocks
        unconditional_call = False
        for stmt in node.body:
            # If the recursive call is directly in a top-level statement (e.g. return rec())
            if not isinstance(stmt, (ast.If, ast.While, ast.For)):
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == fn_name:
                        unconditional_call = True
                        break

        if unconditional_call:
            issues.append({
                "category": "UNGUARDED_RECURSION",
                "severity": "CRITICAL",
                "filename": filename,
                "line": getattr(node, "lineno", 1),
                "message": f"Recursive function '{fn_name}' has no guarded base case return or raise.",
            })

    def remediate_source(self, code: str) -> str:
        """Deterministically remediates unbounded loops by injecting safety counter guards."""
        tree = ast.parse(code)
        transformer = _LoopSafetyTransformer()
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        return ast.unparse(transformed_tree)

    def audit_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Audits a single Python file on disk."""
        if not os.path.isfile(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
            return self.audit_source(code, filepath)
        except Exception as e:
            return [{
                "category": "IO_ERROR",
                "severity": "HIGH",
                "filename": filepath,
                "line": 1,
                "message": str(e),
            }]

    def audit_directory(self, root_dir: str) -> Dict[str, Any]:
        """Audits all Python files in a directory recursively."""
        all_issues: List[Dict[str, Any]] = []
        checked_count = 0

        skip_dirs = {".git", "__pycache__", ".venv", "venv", ".focusgate"}

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
            for fn in filenames:
                if fn.endswith(".py"):
                    full_path = os.path.join(dirpath, fn)
                    file_issues = self.audit_file(full_path)
                    all_issues.extend(file_issues)
                    checked_count += 1

        return {
            "target": root_dir,
            "checked_files": checked_count,
            "is_safe": len(all_issues) == 0,
            "issues": all_issues,
        }
