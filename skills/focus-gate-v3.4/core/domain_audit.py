"""Domain auditor and contract validator (moved out of the CLI script in v3.4)."""
import json
import os

from typing import Any
from typing import Dict
from core.aggregate import DomainEvent


class DomainAuditor:
    """Audits workspace against Domain-Driven Design standards and writing-for-agents doctrine."""

    FORBIDDEN_PROHIBITIONS = [
        "forbidden:",
        "never do",
        "never dump",
        "never delete",
        "never disrupt",
        "never write ahead",
        "never test private",
        "don't do",
        "before sending, delete"
    ]

    DEPRECATED_TERMS = {
        "checklist item": "Tracer Gate",
        "todo item": "Gate",
        "brain dump": "Fragment",
        "chat layout": "Action Envelope",
        "backlog": "Frontier Buffer",
        "current task": "Active Gate",
    }

    @classmethod
    def audit_workspace(cls, target_dir: str = ".") -> Dict[str, Any]:
        results = {
            "status": "PASS",
            "score": 100,
            "ubiquitous_language_violations": [],
            "positive_steering_violations": [],
            "bounded_context_leaks": [],
            "audited_files_count": 0
        }

        for root, _, files in os.walk(target_dir):
            if any(p in root for p in [".git", "__pycache__", "node_modules"]):
                continue
            for fname in files:
                if fname.endswith((".md", ".txt")):
                    fpath = os.path.join(root, fname)
                    results["audited_files_count"] += 1
                    cls._audit_markdown_file(fpath, results)
                elif fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    results["audited_files_count"] += 1
                    cls._audit_python_file(fpath, results)

        if (results["ubiquitous_language_violations"] or
            results["positive_steering_violations"] or
            results["bounded_context_leaks"]):
            results["status"] = "WARN" if results["score"] >= 80 else "FAIL"

        return results

    @classmethod
    def _audit_markdown_file(cls, fpath: str, results: Dict[str, Any]):
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception:
            return

        rel_path = fpath
        is_manifest = "facets" in rel_path or "SKILL.md" in rel_path
        for line_idx, line in enumerate(lines, 1):
            line_lower = line.lower()
            if is_manifest:
                for term in cls.FORBIDDEN_PROHIBITIONS:
                    if term in line_lower:
                        results["positive_steering_violations"].append({
                            "file": rel_path,
                            "line": line_idx,
                            "pattern": term,
                            "content": line.strip()
                        })
                        results["score"] = max(0, results["score"] - 5)

            for dep_term, canonical in cls.DEPRECATED_TERMS.items():
                if f" {dep_term} " in f" {line_lower} " and "_replaces_:" not in line_lower:
                    results["ubiquitous_language_violations"].append({
                        "file": rel_path,
                        "line": line_idx,
                        "deprecated_term": dep_term,
                        "canonical_replacement": canonical,
                        "content": line.strip()
                    })
                    results["score"] = max(0, results["score"] - 2)

    @classmethod
    def _audit_python_file(cls, fpath: str, results: Dict[str, Any]):
        if "prototypes" in fpath or "templates" in fpath:
            return
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception:
            return

        in_docstring = False
        for line_idx, line in enumerate(lines, 1):
            line_strip = line.strip()
            t3 = line_strip.count('"""')
            s3 = line_strip.count("'''")
            if (t3 % 2 != 0) or (s3 % 2 != 0):
                in_docstring = not in_docstring
                continue
            if in_docstring or line_strip.startswith("#") or line_strip.startswith('"') or line_strip.startswith("'"):
                continue
            if "in line" in line or "dom_leaks" in line:
                continue

            if "document.getElementById(" in line or "window.alert(" in line or "document.querySelector(" in line:
                results["bounded_context_leaks"].append({
                    "file": fpath,
                    "line": line_idx,
                    "leak": "DOM Coupling in Python module",
                    "content": line.strip()
                })
                results["score"] = max(0, results["score"] - 5)


class ContractValidator:
    """Validates .focusgate/ledger.events.jsonl against JSON schema contracts."""

    @classmethod
    def validate_events_file(cls, events_path: str) -> Dict[str, Any]:
        if not os.path.exists(events_path):
            return {
                "status": "PASS",
                "total_events": 0,
                "valid_events": 0,
                "invalid_events": 0,
                "errors": [],
                "message": f"Events file {events_path} does not exist yet (clean state)."
            }

        total = 0
        valid = 0
        errors = []

        with open(events_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    data = json.loads(line)
                    is_valid, errs = DomainEvent.validate_schema(data)
                    if is_valid:
                        valid += 1
                    else:
                        errors.append({
                            "line": line_idx,
                            "errors": errs,
                            "raw": line[:80]
                        })
                except json.JSONDecodeError as e:
                    errors.append({
                        "line": line_idx,
                        "errors": [f"Invalid JSON syntax: {str(e)}"],
                        "raw": line[:80]
                    })

        return {
            "status": "PASS" if not errors else "FAIL",
            "total_events": total,
            "valid_events": valid,
            "invalid_events": len(errors),
            "errors": errors,
            "file": events_path
        }
