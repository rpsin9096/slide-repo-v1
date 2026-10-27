"""FocusGate v2.8.5 — Universal Multilingual Anti-Cliché Code Architecture Oracle.

Detects shallow software architecture, AI code generation tells, and unconstrained error handling across:
1. Python:
   - Junk-Drawer Modules (utils.py, helpers.py, common.py with >3 definitions)
   - Shotgun Exception Suppression (except Exception: pass, except: pass)
   - Anemic Passthrough Classes (stateless single-method passthroughs)
2. TypeScript / JavaScript:
   - Shotgun Catch Blocks (empty catch blocks)
   - Unchecked Any Spree (>=3 occurrences of 'as any' or ': any')
   - Junk-Drawer Modules (utils.ts, helpers.ts with >2 exports)
3. Rust:
   - Excessive Unwrap (>2 .unwrap() calls in production code)
   - Incomplete Macro Stubs (todo!() / unimplemented!())

All findings carry actionable prescriptive remedies.
Zero external dependencies (100% Python stdlib).
"""

import ast
import os
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class CodeClicheFinding:
    rule_id: str
    description: str
    line_number: Optional[int] = None
    snippet: Optional[str] = None
    severity: str = "WARNING"  # WARNING or VIOLATION
    filename: Optional[str] = None
    prescribed_remedy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "line_number": self.line_number,
            "snippet": self.snippet,
            "severity": self.severity,
            "filename": self.filename,
            "prescribed_remedy": self.prescribed_remedy
        }


@dataclass
class CodeClicheAuditResult:
    clean: bool
    findings: List[CodeClicheFinding] = field(default_factory=list)
    checked_lines: int = 0

    def summary(self) -> str:
        if self.clean:
            return "CODE_CLICHE_AUDIT_PASS: Zero shallow architecture or shotgun code tells detected."
        rules = set(f.rule_id for f in self.findings)
        return f"CODE_CLICHE_AUDIT_FAIL: Found {len(self.findings)} code tell(s) across rules: {', '.join(sorted(rules))}"


class CodeClicheOracle:
    """Audits source files for shallow abstraction, unconstrained errors, and shotgun coding tells."""

    PY_JUNK_DRAWER_NAMES = {"utils.py", "helpers.py", "common.py", "misc.py", "tools.py"}
    TS_JUNK_DRAWER_NAMES = {
        "utils.ts", "helpers.ts", "common.ts", "misc.ts", "tools.ts",
        "utils.js", "helpers.js", "common.js", "misc.js", "tools.js",
        "utils.tsx", "helpers.tsx", "common.tsx", "utils.jsx", "helpers.jsx"
    }

    @classmethod
    def audit_content(cls, content: str, filename: str = "") -> CodeClicheAuditResult:
        findings: List[CodeClicheFinding] = []
        lines = content.splitlines()
        basename = os.path.basename(filename).lower() if filename else ""
        ext = os.path.splitext(basename)[1].lower() if basename else ""

        if ext in (".ts", ".tsx", ".js", ".jsx"):
            findings = cls._audit_typescript(content, filename, lines, basename)
        elif ext in (".rs",):
            findings = cls._audit_rust(content, filename, lines, basename)
        else:
            findings = cls._audit_python(content, filename, lines, basename)

        return CodeClicheAuditResult(
            clean=(len(findings) == 0),
            findings=findings,
            checked_lines=len(lines)
        )

    @classmethod
    def _audit_python(cls, content: str, filename: str, lines: List[str], basename: str) -> List[CodeClicheFinding]:
        findings: List[CodeClicheFinding] = []

        try:
            tree = ast.parse(content, filename=filename or "<input>")
        except SyntaxError:
            # Skip AST checks if unparseable
            return findings

        # Check for Junk Drawer module names with > 3 functions/classes
        if basename in cls.PY_JUNK_DRAWER_NAMES:
            top_level_defs = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            if len(top_level_defs) > 3:
                findings.append(CodeClicheFinding(
                    rule_id="CODE_JUNK_DRAWER_MODULE",
                    description=f"File '{basename}' is a junk-drawer module containing {len(top_level_defs)} top-level definitions. Decompose into deep, cohesive domain modules.",
                    line_number=1,
                    snippet=f"File: {basename} ({len(top_level_defs)} definitions)",
                    severity="VIOLATION",
                    filename=filename,
                    prescribed_remedy="Decompose into cohesive domain-specific modules (e.g., auth, parsing, validation) instead of a monolithic grab-bag."
                ))

        for node in ast.walk(tree):
            # Check Shotgun Exception Suppression
            if isinstance(node, ast.ExceptHandler):
                is_blanket = False
                if node.type is None:
                    is_blanket = True  # bare except:
                elif isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException"):
                    is_blanket = True

                if is_blanket and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    lineno = getattr(node, "lineno", 1)
                    snippet = lines[lineno - 1].strip() if lineno <= len(lines) else "except Exception: pass"
                    findings.append(CodeClicheFinding(
                        rule_id="CODE_SHOTGUN_SUPPRESSION",
                        description="Shotgun error suppression: blanket 'except Exception: pass' detected. Replace with domain-specific exception handling or logging.",
                        line_number=lineno,
                        snippet=snippet,
                        severity="VIOLATION",
                        filename=filename,
                        prescribed_remedy="Replace blanket 'except Exception:' with specific exception classes (e.g., KeyError, ValueError) or log with traceback."
                    ))

            # Check Anemic Passthrough Classes
            if isinstance(node, ast.ClassDef):
                has_dataclass = any(
                    (isinstance(d, ast.Name) and d.id == "dataclass") or
                    (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass")
                    for d in node.decorator_list
                )
                fields = [f for f in node.body if isinstance(f, (ast.AnnAssign, ast.Assign))]
                methods = [m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if not has_dataclass and not fields and len(methods) == 1 and not node.bases and methods[0].name != "__init__":
                    m = methods[0]
                    if len(m.body) == 1 and isinstance(m.body[0], ast.Return):
                        lineno = getattr(node, "lineno", 1)
                        findings.append(CodeClicheFinding(
                            rule_id="CODE_ANEMIC_PASSTHROUGH_CLASS",
                            description=f"Class '{node.name}' is an anemic single-method passthrough without state or invariants.",
                            line_number=lineno,
                            snippet=f"class {node.name}: ... def {m.name}()",
                            severity="WARNING",
                            filename=filename,
                            prescribed_remedy="Eliminate anemic class and replace with direct function call or enrich with encapsulated state and invariants."
                        ))

        return findings

    @classmethod
    def _audit_typescript(cls, content: str, filename: str, lines: List[str], basename: str) -> List[CodeClicheFinding]:
        findings: List[CodeClicheFinding] = []

        # 1. Junk-Drawer module in TypeScript/JavaScript
        if basename in cls.TS_JUNK_DRAWER_NAMES:
            exports = re.findall(r"^\s*export\s+", content, re.MULTILINE)
            if len(exports) > 2:
                findings.append(CodeClicheFinding(
                    rule_id="CODE_JUNK_DRAWER_MODULE",
                    description=f"File '{basename}' is a junk-drawer module containing {len(exports)} exported definitions. Decompose into cohesive domain modules.",
                    line_number=1,
                    snippet=f"File: {basename} ({len(exports)} exports)",
                    severity="VIOLATION",
                    filename=filename,
                    prescribed_remedy="Decompose into cohesive domain-specific modules (e.g., auth, parsing, validation) instead of a monolithic grab-bag."
                ))

        # 2. Shotgun error suppression (empty catch block)
        for match in re.finditer(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}", content):
            lineno = content[:match.start()].count("\n") + 1
            snippet = lines[lineno - 1].strip() if lineno <= len(lines) else "catch (err) {}"
            findings.append(CodeClicheFinding(
                rule_id="CODE_SHOTGUN_SUPPRESSION_TS",
                description="Shotgun error suppression: empty catch block detected in TypeScript/JavaScript.",
                line_number=lineno,
                snippet=snippet,
                severity="VIOLATION",
                filename=filename,
                prescribed_remedy="Log error with console.error(err) or re-throw a domain-specific exception instead of swallowing."
            ))

        # 3. Unchecked 'any' spree
        any_matches = list(re.finditer(r"(?:\bas\s+any\b|:\s*any\b)", content))
        if len(any_matches) >= 3:
            first = any_matches[0]
            lineno = content[:first.start()].count("\n") + 1
            snippet = lines[lineno - 1].strip() if lineno <= len(lines) else ": any"
            findings.append(CodeClicheFinding(
                rule_id="CODE_UNCHECKED_ANY_SPREE",
                description=f"Unchecked 'any' spree: found {len(any_matches)} occurrences of 'any' circumventing type safety.",
                line_number=lineno,
                snippet=snippet,
                severity="WARNING",
                filename=filename,
                prescribed_remedy="Replace 'any' with unknown, specific interfaces, or generic type constraints to restore static typing."
            ))

        return findings

    @classmethod
    def _audit_rust(cls, content: str, filename: str, lines: List[str], basename: str) -> List[CodeClicheFinding]:
        findings: List[CodeClicheFinding] = []
        is_test = "test" in basename.lower() or "#[cfg(test)]" in content

        # 1. Excessive unconstrained .unwrap()
        if not is_test:
            unwrap_matches = list(re.finditer(r"\.unwrap\(\)", content))
            if len(unwrap_matches) > 2:
                first = unwrap_matches[0]
                lineno = content[:first.start()].count("\n") + 1
                snippet = lines[lineno - 1].strip() if lineno <= len(lines) else ".unwrap()"
                findings.append(CodeClicheFinding(
                    rule_id="CODE_UNCONSTRAINED_UNWRAP_RUST",
                    description=f"Excessive unwrap: found {len(unwrap_matches)} unconstrained .unwrap() calls. Production Rust must propagate or explicitly handle errors.",
                    line_number=lineno,
                    snippet=snippet,
                    severity="VIOLATION",
                    filename=filename,
                    prescribed_remedy="Propagate errors with the '?' operator or handle with match/unwrap_or_else instead of bare .unwrap()."
                ))

        # 2. Todo / unimplemented macro stubs
        for match in re.finditer(r"\b(?:todo!|unimplemented!)\s*\(", content):
            lineno = content[:match.start()].count("\n") + 1
            snippet = lines[lineno - 1].strip() if lineno <= len(lines) else "todo!()"
            findings.append(CodeClicheFinding(
                rule_id="CODE_TODO_STUB_RUST",
                description="Incomplete implementation: todo!() or unimplemented!() macro stub detected.",
                line_number=lineno,
                snippet=snippet,
                severity="VIOLATION",
                filename=filename,
                prescribed_remedy="Implement handler branch or return explicit error rather than panicking on todo!()/unimplemented!()."
            ))

        return findings
