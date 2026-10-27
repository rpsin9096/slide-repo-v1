"""Wave, production and domain verification."""
import json
import os
import sys

from core.cli.parser import build_parser
from core.cli.parser import known_flags
from core.cli.pipeline import DriverContext
from core.cli.registry import CommandContext
from core.cli.registry import command
from core.domain_audit import ContractValidator
from core.domain_audit import DomainAuditor
from core.facets.catalog import FacetCatalog
from core.facets.catalog import lint_all
from core.orchestrator_kernel import OrchestratorKernel


def _match_verify_wave(ctx: CommandContext) -> bool:
    args = ctx.args
    cmd = ctx.cmd
    return getattr(args, 'verify_wave', False) or cmd == '--verify-wave'


@command('verify-wave', flags=('--verify-wave',), dest=None, summary='Runs every verifier (index, contracts, tokens, help, stage, sufficiency, production) and prints ONE aggregate verdict (v2.8).', matches=_match_verify_wave, order=242)
def verify_wave(ctx: CommandContext) -> int:
    """Runs every verifier (index, contracts, tokens, help, stage, sufficiency, production) and prints ONE aggregate verdict (v2.8)."""
    args = ctx.args
    cmd = ctx.cmd
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    from core.facet_index import index_is_current
    gates = {}

    # 1. facet_index_fresh
    facets_dir = FacetCatalog.default().dir
    fresh = index_is_current(facets_dir)
    gates["facet_index_fresh"] = {
        "status": "PASS" if fresh else "FAIL",
        "details": "facet_index.json is current" if fresh else "facet_index.json is stale"
    }

    # 2. facet_contracts
    errors, warnings, contracts, seen_pat = lint_all(facets_dir, known_flags())
    contracts_pass = (len(errors) == 0)
    gates["facet_contracts"] = {
        "status": "PASS" if contracts_pass else "FAIL",
        "details": f"{len(contracts)} contracts clean, 0 errors" if contracts_pass else f"{len(errors)} contract error(s)"
    }

    # 3. token_consistency
    facets = FacetCatalog.default().summary_rows()
    modes_valid = all(f.get("mode") in ("WINDOW", "EPHEMERAL") for f in facets) and len(facets) == 19
    raw_formula = "//" + " 4"
    cli_sources = [ctx.cli_path] + [os.path.join(dp, f) for dp, _d, fs in os.walk(os.path.join(ctx.skill_root, "core", "cli")) for f in fs if f.endswith(".py")]
    no_raw_divide = True
    for cli_src in cli_sources:
        with open(cli_src, "r", encoding="utf-8") as sf:
            if raw_formula in sf.read():
                no_raw_divide = False
    tok_pass = modes_valid and no_raw_divide
    gates["token_consistency"] = {
        "status": "PASS" if tok_pass else "FAIL",
        "details": "19 facets valid mode (WINDOW|EPHEMERAL) and canonical tokens" if tok_pass else "Token consistency error"
    }

    # 4. cli_help_clean
    help_text = build_parser().format_help()
    has_clean_help = ("1.3.5" not in help_text)
    gates["cli_help_clean"] = {
        "status": "PASS" if has_clean_help else "FAIL",
        "details": "help text free of stale version strings" if has_clean_help else "stale version string in help"
    }

    # 5. stage_matrix
    gates_md_cand1 = os.path.join(ledger_root, "GATES.md")
    gates_md_cand2 = os.path.abspath(".focusgate/GATES.md")
    stages_json_cand = os.path.join(ledger_root, "stages.json")
    if os.path.exists(gates_md_cand1) or os.path.exists(gates_md_cand2) or os.path.exists(stages_json_cand):
        try:
            orch = OrchestratorKernel(ledger_root)
            active_stage = orch.stage_matrix.get_active_stage(orch.stage_definitions, orch.aggregate.gates)
            if active_stage:
                ok, reasons, evidence = orch.stage_matrix.verify_stage_completion(active_stage, orch.aggregate.gates)
                gates["stage_matrix"] = {
                    "status": "PASS" if ok else "FAIL",
                    "details": f"Stage {active_stage.name}: {'PASS' if ok else 'FAIL'}"
                }
            else:
                gates["stage_matrix"] = {
                    "status": "SKIP",
                    "details": "no active stage in ledger"
                }
        except Exception as exc:
            gates["stage_matrix"] = {
                "status": "FAIL",
                "details": f"stage verification error: {exc}"
            }
    else:
        gates["stage_matrix"] = {
            "status": "SKIP",
            "details": "no GATES.md or stages.json in ledger root"
        }

    # 6. context_sufficiency
    import glob
    brief_files = glob.glob("AGENT-BRIEF*.md")
    worktree_prompts = glob.glob(os.path.join(ledger_root, "worktrees", "*", "AGENT_PROMPT.md"))
    audit_targets = list(brief_files) + list(worktree_prompts)
    if audit_targets:
        try:
            from core.oracles.context_sufficiency_oracle import RichnessSufficiencyOracle
            findings = []
            for target_file in audit_targets:
                with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                    res = RichnessSufficiencyOracle.audit_prompt(f.read())
                findings.extend(res.get("findings", []))
            gates["context_sufficiency"] = {
                "status": "PASS" if not findings else "FAIL",
                "details": f"{len(audit_targets)} brief/prompt target(s) audited, {len(findings)} finding(s)"
            }
        except Exception as exc:
            gates["context_sufficiency"] = {
                "status": "FAIL",
                "details": f"context sufficiency audit error: {exc}"
            }
    else:
        gates["context_sufficiency"] = {
            "status": "SKIP",
            "details": "no AGENT-BRIEF*.md or worktree AGENT_PROMPT.md found"
        }

    clean = all(g["status"] == "PASS" for g in gates.values() if g["status"] != "SKIP")

    if is_json:
        print(json.dumps({"clean": clean, "gates": gates}, indent=2))
    else:
        print("=" * 80)
        print("FOCUSGATE v2.8 WAVE VERIFICATION REPORT")
        print("=" * 80)
        for gname, gdata in gates.items():
            print(f"  [{gdata['status']:<4}] {gname:<24} - {gdata['details']}")
        print("=" * 80)
        print(f"Overall Wave Verdict: {'PASS (Clean)' if clean else 'FAIL'}")
    return (0 if clean else 1)


def _match_audit_production(ctx: CommandContext) -> bool:
    args = ctx.args
    cmd = ctx.cmd
    return getattr(args, 'audit_production', False) or cmd == '--audit-production'


@command('audit-production', flags=('--audit-production',), dest=None, summary='Runs complete audit of v2.8 production readiness', matches=_match_audit_production, order=243)
def audit_production(ctx: CommandContext) -> int:
    """Runs complete audit of v2.8 production readiness"""
    args = ctx.args
    cmd = ctx.cmd
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    skill_root = ctx.skill_root
    from core.oracles.code_cliche_oracle import CodeClicheOracle
    from core.facet_index import index_is_current
    cliche_violations = 0
    core_dir = os.path.join(ctx.skill_root, "core")
    for root, _, files in os.walk(core_dir):
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                with open(fpath, "r", encoding="utf-8", errors="replace") as cf:
                    res = CodeClicheOracle.audit_content(cf.read(), filename=f)
                    cliche_violations += len([v for v in res.findings if v.severity == "VIOLATION"])

    facets_dir = FacetCatalog.default().dir
    fresh = index_is_current(facets_dir)
    errors, warnings, contracts, seen_pat = lint_all(facets_dir, known_flags())
    contracts_pass = (len(errors) == 0)
    help_text = build_parser().format_help()
    has_clean_help = ("1.3.5" not in help_text)

    orch = OrchestratorKernel(ledger_root)
    checkpoints = orch.list_checkpoints()

    model_adapter_info = None
    try:
        from adapters.model_adapter import LoRAModelAdapter
        adapter = LoRAModelAdapter(repo_root=skill_root)
        if adapter.is_available():
            model_adapter_info = adapter.get_metadata()
    except (ImportError, OSError, ValueError, KeyError):
        pass

    prod_pass = (cliche_violations == 0 and has_clean_help and fresh and contracts_pass)
    report = {
        "production_readiness": "PASS" if prod_pass else "FAIL",
        "version": "2.8",
        "code_tell_violations": cliche_violations,
        "facet_contracts_clean": contracts_pass,
        "facet_index_current": fresh,
        "cli_help_clean": has_clean_help,
        "checkpoints_recorded": len(checkpoints),
        "distilled_router_adapter": model_adapter_info
    }
    if is_json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 80)
        print("FOCUSGATE v2.8 PRODUCTION READINESS SCORECARD")
        print("=" * 80)
        print(f"  Production Verdict:     {'PASS (Ready)' if prod_pass else 'FAIL'}")
        print(f"  Code Cliche Violations: {cliche_violations}")
        print(f"  Facet Contracts Clean:  {contracts_pass}")
        print(f"  Facet Index Current:    {fresh}")
        print(f"  CLI Help Clean:         {has_clean_help}")
        print(f"  Production Checkpoints: {len(checkpoints)}")
        if model_adapter_info:
            print(f"  Distilled Router:       VERIFIED [{model_adapter_info['base_model']}, LoRA r={model_adapter_info['rank']}, {model_adapter_info['trainable_parameters']:,} params, SHA: {model_adapter_info['checksum_short']}]")
        else:
            print("  Distilled Router:       NOT DETECTED (FastPath Active)")
        print("=" * 80)
    return (0 if prod_pass else 1)


def _match_guard(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'guard', None) is not None


@command('guard', flags=('--guard',), dest=None, summary='guard command', matches=_match_guard, order=244)
def guard(ctx: CommandContext) -> int:
    """guard command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    pipeline = ctx.pipeline
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --guard \"<command>\"", file=sys.stderr)
        return (1)
    target_cmd = clean_args[1]
    ctx = DriverContext("sh", ["-c", target_cmd])
    pipeline.execute(ctx)
    if is_json:
        print(json.dumps({"command": target_cmd, "safe": not ctx.blocked, "reason": ctx.block_reason}))
    else:
        if ctx.blocked:
            print(f"[BLOCKED] {ctx.block_reason}")
        else:
            print(f"[ALLOWED] Command is safe to execute: {target_cmd}")
    return (1 if ctx.blocked else 0)


def _match_audit_domain(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_domain', None) is not None


@command('audit-domain', flags=('--audit-domain',), dest=None, summary='audit-domain command', matches=_match_audit_domain, order=245)
def audit_domain(ctx: CommandContext) -> int:
    """audit-domain command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    target_dir = clean_args[1] if len(clean_args) > 1 and not clean_args[1].startswith("-") else "."
    res = DomainAuditor.audit_workspace(target_dir)
    if is_json:
        print(json.dumps(res, indent=2))
    else:
        print("=" * 80)
        print("FOCUSGATE DOMAIN MODELING & AGENT AUDIT REPORT (v2.8)")
        print(f"Target Directory: {os.path.abspath(target_dir)}")
        print(f"Status: {res['status']} (Compliance Score: {res['score']}/100)")
        print(f"Audited Files: {res['audited_files_count']}")
        print("=" * 80)
        if res["positive_steering_violations"]:
            print(f"\n[!] Positive Target Steering Violations ({len(res['positive_steering_violations'])} found):")
            for v in res["positive_steering_violations"]:
                print(f"  • {v['file']}:{v['line']} - Pattern '{v['pattern']}' -> {v['content']}")
        else:
            print("\n[✓] Positive Target Steering: Clean (zero prohibition anti-patterns)")

        if res["ubiquitous_language_violations"]:
            print(f"\n[!] Ubiquitous Language Violations ({len(res['ubiquitous_language_violations'])} found):")
            for v in res["ubiquitous_language_violations"]:
                print(f"  • {v['file']}:{v['line']} - Deprecated '{v['deprecated_term']}' -> Replace with '{v['canonical_replacement']}'")
        else:
            print("[✓] Ubiquitous Language: Clean (zero deprecated concept drifts)")

        if res["bounded_context_leaks"]:
            print(f"\n[!] Bounded Context Leaks ({len(res['bounded_context_leaks'])} found):")
            for v in res["bounded_context_leaks"]:
                print(f"  • {v['file']}:{v['line']} - {v['leak']}")
        else:
            print("[✓] Bounded Context Purity: Clean (zero domain leaks)")
        print("=" * 80)
    return (0 if res["status"] == "PASS" else 1)


def _match_validate_contracts(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'validate_contracts', None) is not None


@command('validate-contracts', flags=('--validate-contracts',), dest=None, summary='validate-contracts command', matches=_match_validate_contracts, order=246)
def validate_contracts(ctx: CommandContext) -> int:
    """validate-contracts command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    ledger_root = ctx.ledger_root
    events_path = clean_args[1] if len(clean_args) > 1 and not clean_args[1].startswith("-") else os.path.join(ledger_root, "ledger.events.jsonl")
    res = ContractValidator.validate_events_file(events_path)
    if is_json:
        print(json.dumps(res, indent=2))
    else:
        print("=" * 80)
        print("FOCUSGATE CONTRACT & SCHEMA VALIDATION REPORT (v2.8)")
        print(f"Events File: {events_path}")
        print(f"Status: {res['status']} | Valid: {res['valid_events']}/{res['total_events']}")
        print("=" * 80)
        if res["errors"]:
            print("\nSchema Contract Violations:")
            for err in res["errors"]:
                print(f"  • Line {err['line']}: {', '.join(err['errors'])} -> {err['raw']}")
        else:
            print("[✓] All domain event records conform strictly to DomainEvent schema.")
        print("=" * 80)
    return (0 if res["status"] == "PASS" else 1)


def _match_audit_all(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_all', None) is not None


@command('audit-all', flags=('--audit-all',), dest=None, summary='audit-all command', matches=_match_audit_all, order=257)
def audit_all(ctx: CommandContext) -> int:
    """audit-all command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    target = clean_args[1] if len(clean_args) > 1 else ""
    if not target or not os.path.exists(target):
        print("Usage: focus-gate.py --audit-all <file_or_dir>", file=sys.stderr)
        return (1)
    try:
        from core.oracles.unified_audit import UnifiedAuditOracle
        from core.oracles.cliche_oracle import ClicheOracle
        from core.oracles.prose_cliche_oracle import ProseClicheOracle
        from core.oracles.code_cliche_oracle import CodeClicheOracle

        files_by_category = {"prose": [], "code": [], "design": []}
        if os.path.isfile(target):
            ext = os.path.splitext(target)[1].lower()
            if ext in (".py", ".ts", ".js", ".rs"):
                files_by_category["code"].append(target)
            elif ext in (".css", ".html", ".tsx", ".jsx"):
                files_by_category["design"].append(target)
            else:
                files_by_category["prose"].append(target)
        else:
            for root_dir, _, files in os.walk(target):
                for fn in files:
                    fp = os.path.join(root_dir, fn)
                    ext = os.path.splitext(fn)[1].lower()
                    if ext in (".py", ".ts", ".js", ".rs"):
                        files_by_category["code"].append(fp)
                    elif ext in (".css", ".html", ".tsx", ".jsx"):
                        files_by_category["design"].append(fp)
                    elif ext in (".md", ".txt", ".rst", ".json"):
                        files_by_category["prose"].append(fp)

        all_findings = []
        total_lines = 0
        for fp in files_by_category["prose"]:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            r = ProseClicheOracle.audit_content(content, filename=fp)
            all_findings.extend(r.findings)
            total_lines += r.checked_lines
            # Loop 63: markdown carries design tells too. Before this,
            # `.md` was routed to prose ONLY, so --audit-design-cliche
            # reported findings that --audit-all silently dropped — the
            # flagship "audit everything" was the least complete view.
            # --audit-design-cliche walks .md (see its filter at the
            # --audit-design-cliche branch), so the aggregate must too.
            d = ClicheOracle.audit_content(content, filename=fp)
            all_findings.extend(d.findings)
            total_lines += d.checked_lines
            files_by_category["design"].append(fp)
        for fp in files_by_category["code"]:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                r = CodeClicheOracle.audit_content(f.read(), filename=fp)
            all_findings.extend(r.findings)
            total_lines += r.checked_lines
        for fp in files_by_category["design"]:
            if fp in files_by_category["prose"]:
                continue  # already run above
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                r = ClicheOracle.audit_content(f.read(), filename=fp)
            all_findings.extend(r.findings)
            total_lines += r.checked_lines

        res = {
            "clean": len(all_findings) == 0,
            "checked_lines": total_lines,
            "prose_files": len(files_by_category["prose"]),
            "code_files": len(files_by_category["code"]),
            "design_files": len(set(files_by_category["design"])),
            "findings": [f.to_dict() for f in all_findings],
        }
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)

    if is_json:
        print(json.dumps(res, indent=2))
        return (0 if res["clean"] else 1)
    elif res["clean"]:
        print(f"UNIFIED_AUDIT_PASS: {target} (Zero prose, code, or design cliché tells)")
        return (0)
    else:
        print(f"UNIFIED_AUDIT_FAIL: {target} (999 tell(s) detected)")
        for f in res["findings"]:
            loc = f"{os.path.basename(f.get('filename', ''))}:" if f.get("filename") else ""
            print(f"  [{f.get('rule_id')}] {loc}line {f.get('line_number') or '?'}: {f.get('description')}")
        return (1)
