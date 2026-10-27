"""Oracle audits: contrast, tokens, cliches, context sufficiency, safe zone, handoffs, patches, rigor."""
import json
import os
import sys

from adapters.oracle_adapter import ContrastOracleAdapter
from core.cli.documents import collect_documents
from core.cli.registry import CommandContext
from core.cli.registry import command
from core.kernel import FocusKernel
from core.oracles.safe_zone import SafeZoneValidator
from core.oracles.token_engine import DesignTokenEngine
from core.tool_matrix import ToolSelectionMatrix
from core.unlazy_guard import ExecutionRigorGuard
from plugins.cognitive_plugin import CognitivePlugin
from plugins.design_plugin import DesignPlugin
from plugins.engineering_plugin import EngineeringPlugin
from plugins.writing_plugin import WritingPlugin


def _match_audit_contrast(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_contrast', None) is not None


@command('audit-contrast', flags=('--audit-contrast',), dest=None, summary='audit-contrast command', matches=_match_audit_contrast, order=251)
def audit_contrast(ctx: CommandContext) -> int:
    """audit-contrast command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 3:
        print("Usage: focus-gate.py --audit-contrast <fg_color> <bg_color>", file=sys.stderr)
        return (1)
    fg = clean_args[1]
    bg = clean_args[2]
    try:
        res = ContrastOracleAdapter.verdict(fg, bg)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)
    if is_json:
        print(json.dumps(res, indent=2))
    else:
        verdict = "CONTRAST_PASS_AA" if res["pass_aa"] else "CONTRAST_FAIL_AA"
        print(f"{verdict} ratio={res['ratio']:.2f} fg={res['fg']} bg={res['bg']}")
    return (0 if res["pass_aa"] else 1)


def _match_audit_tokens(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_tokens', None) is not None


@command('audit-tokens', flags=('--audit-tokens',), dest=None, summary='audit-tokens command', matches=_match_audit_tokens, order=252)
def audit_tokens(ctx: CommandContext) -> int:
    """audit-tokens command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --audit-tokens <target_path>", file=sys.stderr)
        return (1)
    target = clean_args[1]
    try:
        res = DesignTokenEngine.audit(target)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)
    if is_json:
        print(json.dumps(res, indent=2))
        return (0 if res["passed"] else 1)
    elif res["passed"]:
        print(f"AUDIT_TOKENS_PASS {res['path']}")
        return (0)
    else:
        print(f"AUDIT_TOKENS_FAIL {res['path']} {len(res['violations'])} violation(s)")
        for v in res["violations"]:
            print(f"  line {v['line']}: [{v['kind']}] {v['match']}")
        return (1)


def _match_audit_design_cliche(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_design_cliche', None) is not None


@command('audit-design-cliche', flags=('--audit-design-cliche',), dest=None, summary='audit-design-cliche command', matches=_match_audit_design_cliche, order=253)
def audit_design_cliche(ctx: CommandContext) -> int:
    """audit-design-cliche command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    target = clean_args[1] if len(clean_args) > 1 else ""
    if not target or not os.path.exists(target):
        print("Usage: focus-gate.py --audit-design-cliche <file_or_dir>", file=sys.stderr)
        return (1)
    try:
        from core.oracles.cliche_oracle import ClicheOracle, ClicheAuditResult
        if os.path.isfile(target):
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            res = ClicheOracle.audit_content(content, filename=target)
        else:
            findings = []
            total_lines = 0
            for root_dir, _, files in os.walk(target):
                for fn in files:
                    if fn.endswith((".css", ".html", ".tsx", ".jsx", ".md")):
                        fp = os.path.join(root_dir, fn)
                        with open(fp, "r", encoding="utf-8", errors="replace") as f:
                            c = f.read()
                        r = ClicheOracle.audit_content(c, filename=fp)
                        findings.extend(r.findings)
                        total_lines += r.checked_lines
            res = ClicheAuditResult(clean=len(findings) == 0, findings=findings, checked_lines=total_lines)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)

    if is_json:
        print(json.dumps({"clean": res.clean, "summary": res.summary(), "findings": [f.to_dict() for f in res.findings]}, indent=2))
        return (0 if res.clean else 1)
    elif res.clean:
        print(f"CLICHE_AUDIT_PASS: {target} (Zero generic AI design tells detected)")
        return (0)
    else:
        print(f"CLICHE_AUDIT_FAIL: {target} ({len(res.findings)} tell(s) detected)")
        for f in res.findings:
            # v3.2 Loop 63: name the file. "line 369" with no file is not
            # actionable, and without it finding identity cannot be
            # compared against --audit-all.
            loc = f"{os.path.basename(f.filename)}:" if getattr(f, "filename", None) else ""
            print(f"  [{f.rule_id}] {loc}line {f.line_number or '?'}: {f.description} ('{f.snippet}')")
        return (1)


def _match_audit_prose_cliche(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_prose_cliche', None) is not None


@command('audit-prose-cliche', flags=('--audit-prose-cliche',), dest=None, summary='audit-prose-cliche command', matches=_match_audit_prose_cliche, order=254)
def audit_prose_cliche(ctx: CommandContext) -> int:
    """audit-prose-cliche command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    target = clean_args[1] if len(clean_args) > 1 else ""
    if not target or not os.path.exists(target):
        print("Usage: focus-gate.py --audit-prose-cliche <file_or_dir>", file=sys.stderr)
        return (1)
    try:
        from core.oracles.prose_cliche_oracle import ProseClicheOracle, ProseClicheAuditResult
        if os.path.isfile(target):
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            res = ProseClicheOracle.audit_content(content, filename=target)
        else:
            # v3.2 Loop 66: this branch used to carry its OWN inline
            # walker, separate from `collect_documents`, and it included
            # .json — so auditing the workspace scored `evals/evals.json`,
            # whose entire purpose is to name the buzzwords the prose
            # oracle detects. The oracle was reporting its own fixture.
            # Route through the shared walk so every flag agrees on what a
            # directory contains, and skip generated/fixture corpora.
            findings = []
            total_lines = 0
            for fp in collect_documents(target):
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    c = f.read()
                r = ProseClicheOracle.audit_content(c, filename=fp)
                findings.extend(r.findings)
                total_lines += r.checked_lines
            res = ProseClicheAuditResult(clean=len(findings) == 0, findings=findings, checked_lines=total_lines)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)

    if is_json:
        print(json.dumps({"clean": res.clean, "summary": res.summary(), "findings": [f.to_dict() for f in res.findings]}, indent=2))
        return (0 if res.clean else 1)
    elif res.clean:
        print(f"PROSE_CLICHE_AUDIT_PASS: {target} (Zero generic AI writing tells detected)")
        return (0)
    else:
        print(f"PROSE_CLICHE_AUDIT_FAIL: {target} ({len(res.findings)} tell(s) detected)")
        for f in res.findings:
            loc = f"{os.path.basename(f.filename)}:" if getattr(f, 'filename', None) else ""
            print(f"  [{f.rule_id}] {loc}line {f.line_number or '?'}: {f.description} ('{f.snippet}')")
        return (1)


def _match_audit_code_cliche(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_code_cliche', None) is not None


@command('audit-code-cliche', flags=('--audit-code-cliche',), dest=None, summary='audit-code-cliche command', matches=_match_audit_code_cliche, order=255)
def audit_code_cliche(ctx: CommandContext) -> int:
    """audit-code-cliche command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    target = clean_args[1] if len(clean_args) > 1 else ""
    if not target or not os.path.exists(target):
        print("Usage: focus-gate.py --audit-code-cliche <file_or_dir>", file=sys.stderr)
        return (1)
    try:
        from core.oracles.code_cliche_oracle import CodeClicheOracle, CodeClicheAuditResult
        if os.path.isfile(target):
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            res = CodeClicheOracle.audit_content(content, filename=target)
        else:
            findings = []
            total_lines = 0
            for root_dir, _, files in os.walk(target):
                for fn in files:
                    if fn.endswith(".py"):
                        fp = os.path.join(root_dir, fn)
                        with open(fp, "r", encoding="utf-8", errors="replace") as f:
                            c = f.read()
                        r = CodeClicheOracle.audit_content(c, filename=fp)
                        findings.extend(r.findings)
                        total_lines += r.checked_lines
            res = CodeClicheAuditResult(clean=len(findings) == 0, findings=findings, checked_lines=total_lines)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)

    if is_json:
        print(json.dumps({"clean": res.clean, "summary": res.summary(), "findings": [f.to_dict() for f in res.findings]}, indent=2))
        return (0 if res.clean else 1)
    elif res.clean:
        print(f"CODE_CLICHE_AUDIT_PASS: {target} (Zero shallow architecture or shotgun code tells detected)")
        return (0)
    else:
        print(f"CODE_CLICHE_AUDIT_FAIL: {target} ({len(res.findings)} tell(s) detected)")
        for f in res.findings:
            loc = f"{os.path.basename(f.filename)}:" if getattr(f, 'filename', None) else ""
            print(f"  [{f.rule_id}] {loc}line {f.line_number or '?'}: {f.description} ('{f.snippet}')")
        return (1)


def _match_audit_context_sufficiency(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_context_sufficiency', None) is not None


@command('audit-context-sufficiency', flags=('--audit-context-sufficiency',), dest=None, summary='audit-context-sufficiency command', matches=_match_audit_context_sufficiency, order=258)
def audit_context_sufficiency(ctx: CommandContext) -> int:
    """audit-context-sufficiency command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    target = clean_args[1] if len(clean_args) > 1 else ""
    if not target or not os.path.exists(target):
        print("Usage: focus-gate.py --audit-context-sufficiency <file_or_dir>", file=sys.stderr)
        return (1)
    try:
        from core.oracles.context_sufficiency_oracle import RichnessSufficiencyOracle
        files = []
        if os.path.isfile(target):
            files.append(target)
        else:
            for root_dir, _, fs in os.walk(target):
                for fn in fs:
                    if fn.lower().endswith(".md"):
                        files.append(os.path.join(root_dir, fn))
        all_findings = []
        audited = 0
        for fp in files:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                res = RichnessSufficiencyOracle.audit_prompt(f.read())
            audited += 1
            for d in res["findings"]:
                merged = dict(d)
                merged["filename"] = fp
                all_findings.append(merged)
        verdict = {"clean": len(all_findings) == 0, "audited_files": audited, "findings": all_findings}
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)

    if is_json:
        print(json.dumps(verdict, indent=2))
        return (0 if verdict["clean"] else 1)
    elif verdict["clean"]:
        print(f"CONTEXT_SUFFICIENCY_PASS: {target} ({audited} brief(s), zero bare pointers / lost summaries)")
        return (0)
    else:
        print(f"CONTEXT_SUFFICIENCY_FAIL: {target} ({len(all_findings)} sufficiency finding(s))")
        for d in all_findings:
            print(f"  [{d.get('kind')}] {os.path.basename(d.get('filename', ''))}: gate {d.get('gate')} -> {d.get('detail')}")
        return (1)


def _match_sync_tokens(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'sync_tokens', None) is not None


@command('sync-tokens', flags=('--sync-tokens',), dest=None, summary='sync-tokens command', matches=_match_sync_tokens, order=259)
def sync_tokens(ctx: CommandContext) -> int:
    """sync-tokens command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --sync-tokens <brand_md> [--out <output_dir>]", file=sys.stderr)
        return (1)
    brand_md = clean_args[1]
    out_dir = "assets"
    if '--out' in clean_args:
        o_idx = clean_args.index('--out')
        if o_idx + 1 < len(clean_args):
            out_dir = clean_args[o_idx + 1]
    try:
        res = DesignTokenEngine.sync(brand_md, out_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)
    if is_json:
        print(json.dumps(res, indent=2))
    else:
        print(f"TOKEN_SYNC_OK json={res['json']} css={res['css']}")
    return (0)


def _match_audit_safe_zone(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_safe_zone', None) is not None


@command('audit-safe-zone', flags=('--audit-safe-zone',), dest=None, summary='audit-safe-zone command', matches=_match_audit_safe_zone, order=260)
def audit_safe_zone(ctx: CommandContext) -> int:
    """audit-safe-zone command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 2:
        print("Usage: focus-gate.py --audit-safe-zone <spec_path> [--platform <platform>] [--box <x,y,w,h>]", file=sys.stderr)
        return (1)
    spec_path = clean_args[1]
    platform = "landscape-16x9"
    if '--platform' in clean_args:
        p_idx = clean_args.index('--platform')
        if p_idx + 1 < len(clean_args):
            platform = clean_args[p_idx + 1]
    # A directory is not a dimension spec. Before Loop 63 this reached
    # parse_dims('.') and reported "Cannot parse dimensions from '.'",
    # which reads like the user's format was wrong. The workspace is the
    # natural argument for a flag documented as a workspace command, so the
    # SVG files in it are what it should mean.
    if os.path.isdir(spec_path):
        svgs = sorted(
            os.path.join(r, fn)
            for r, _, fs in os.walk(spec_path)
            for fn in fs if fn.lower().endswith(".svg"))
        if not svgs:
            print("ERROR: %s is a directory and contains no .svg file; "
                      "--audit-safe-zone needs an .svg path or a WxH spec "
                      "(e.g. 1200x630)" % spec_path, file=sys.stderr)
            return (2)
        failures, checked = [], 0
        for svg in svgs:
            try:
                w, h = SafeZoneValidator.parse_dims(svg)
            except ValueError as exc:
                failures.append("%s: %s" % (svg, exc))
                continue
            res = SafeZoneValidator.check(w, h, platform)
            checked += 1
            if not res.get("safe", True):
                failures.append("%s: %s" % (svg, res.get("reason", "outside safe zone")))
        if not failures:
            print("SAFE_ZONE_PASS: %s (%d .svg file(s) inside the %s safe zone)"
                  % (spec_path, checked, platform))
            return (0)
        print("SAFE_ZONE_FAIL: %s (%d of %d .svg file(s) outside the %s safe zone)"
              % (spec_path, len(failures), checked + len(failures), platform))
        for f in failures:
            print("  - %s" % f)
        return (1)
    try:
        width, height = SafeZoneValidator.parse_dims(spec_path)
        if '--box' in clean_args:
            b_idx = clean_args.index('--box')
            if b_idx + 1 < len(clean_args):
                x, y, w, h = (float(n.strip()) for n in clean_args[b_idx + 1].split(','))
                ok = SafeZoneValidator.contains(width, height, platform, {"x": x, "y": y, "w": w, "h": h})
                res = {"platform": platform, "width": width, "height": height, "box": {"x": x, "y": y, "w": w, "h": h}, "pass": ok}
            else:
                res = SafeZoneValidator.check(width, height, platform)
        else:
            res = SafeZoneValidator.check(width, height, platform)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return (2)
    if is_json:
        print(json.dumps(res, indent=2))
    else:
        status = "SAFE_ZONE_PASS" if res["pass"] else "SAFE_ZONE_FAIL"
        print(f"{status} platform={res['platform']} {int(width) if width.is_integer() else width}x{int(height) if height.is_integer() else height}")
    return (0 if res["pass"] else 1)


def _match_handoff(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'handoff', None) is not None


@command('handoff', flags=('--handoff',), dest=None, summary='handoff command', matches=_match_handoff, order=261)
def handoff(ctx: CommandContext) -> int:
    """handoff command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    kernel = ctx.kernel
    if len(clean_args) < 3:
        print("Usage: focus-gate.py --handoff <source_skill> <target_skill> [--data <json>]", file=sys.stderr)
        return (1)
    src_id = clean_args[1]
    tgt_id = clean_args[2]
    delta_data = {}
    for i, a in enumerate(clean_args):
        if a in ('--data', '-d') and i + 1 < len(clean_args):
            try:
                delta_data = json.loads(clean_args[i + 1])
            except Exception:
                delta_data = {"raw": clean_args[i + 1]}
    kernel = FocusKernel(workspace_root=os.getcwd()) if FocusKernel else None
    if kernel:
        if EngineeringPlugin: kernel.register_plugin(EngineeringPlugin())
        if CognitivePlugin: kernel.register_plugin(CognitivePlugin())
        if DesignPlugin: kernel.register_plugin(DesignPlugin())
        if WritingPlugin: kernel.register_plugin(WritingPlugin())
        kernel.boot()
        verdict = kernel.perform_handoff(src_id, tgt_id, delta_data)
        if is_json:
            print(json.dumps({
                "source": src_id,
                "target": tgt_id,
                "accepted": verdict.accepted,
                "reason": verdict.reason,
                "adapted_payload": verdict.adapted_payload,
                "tokens": getattr(verdict, "tokens", 0)
            }, indent=2))
        else:
            status_str = "ACCEPTED" if verdict.accepted else "REJECTED"
            print(f"Handoff [{src_id} -> {tgt_id}]: {status_str}")
            print(f"Reason: {verdict.reason}")
            print(f"Adapted Payload: {json.dumps(verdict.adapted_payload)}")
        return (0 if verdict.accepted else 1)
    else:
        print("FocusKernel not available.", file=sys.stderr)
        return (1)


def _match_audit_handoffs(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'audit_handoffs', None) is not None


@command('audit-handoffs', flags=('--audit-handoffs',), dest=None, summary='audit-handoffs command', matches=_match_audit_handoffs, order=262)
def audit_handoffs(ctx: CommandContext) -> int:
    """audit-handoffs command"""
    args = ctx.args
    is_json = ctx.is_json
    kernel = ctx.kernel
    kernel = FocusKernel(workspace_root=os.getcwd()) if FocusKernel else None
    if kernel:
        if EngineeringPlugin: kernel.register_plugin(EngineeringPlugin())
        if CognitivePlugin: kernel.register_plugin(CognitivePlugin())
        if DesignPlugin: kernel.register_plugin(DesignPlugin())
        if WritingPlugin: kernel.register_plugin(WritingPlugin())
        kernel.boot()
        report = kernel.audit_handoff_performance()
        if is_json:
            print(json.dumps(report, indent=2))
        else:
            print("FocusGate v2.8 Sub-Skill Handoff Benchmark (<0.05ms, <=120 tokens, SHA-256):")
            print(f"{'Source':<14} {'Target':<14} {'Latency':<12} {'Tokens':<8} {'Checksum':<10} {'Status'}")
            print("-" * 72)
            for h in report["handoffs"]:
                stat = "PASS" if h["accepted"] else "FAIL"
                lat_str = f"{h['latency_ms']:.3f}ms"
                cs_str = "VALID" if h.get("checksum_valid", True) else "INVALID"
                print(f"{h['source']:<14} {h['target']:<14} {lat_str:<12} {h['tokens']:<8} {cs_str:<10} {stat}")
        return (0)
    else:
        print("FocusKernel not available.", file=sys.stderr)
        return (1)


def _match_patch_lint(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'patch_lint', None) is not None


@command('patch-lint', flags=('--patch-lint',), dest=None, summary='patch-lint command', matches=_match_patch_lint, order=265)
def patch_lint(ctx: CommandContext) -> int:
    """patch-lint command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    if len(clean_args) < 3:
        print("Usage: focus-gate.py --patch-lint <target_file> '<search_block>' [--start <line>] [--end <line>]", file=sys.stderr)
        return (1)
    target_path = clean_args[1]
    search_block = clean_args[2]
    s_line = None
    e_line = None
    for i, a in enumerate(clean_args):
        if a == '--start' and i + 1 < len(clean_args):
            s_line = int(clean_args[i + 1])
        elif a == '--end' and i + 1 < len(clean_args):
            e_line = int(clean_args[i + 1])
    if ToolSelectionMatrix:
        matrix = ToolSelectionMatrix(workspace_root=os.getcwd())
        check = matrix.verify_patch_preconditions(target_path, search_block, start_line=s_line, end_line=e_line)
        if is_json:
            print(json.dumps({
                "valid": check.valid,
                "reason": check.reason,
                "file_exists": check.file_exists,
                "exact_match_found": check.exact_match_found,
                "occurrence_count": check.occurrence_count,
                "matched_start_line": check.matched_start_line,
                "matched_end_line": check.matched_end_line,
                "suggested_expanded_range": check.suggested_expanded_range
            }, indent=2))
        else:
            status = "PASS (Safe to patch)" if check.valid else "FAIL (Patch will fail)"
            print(f"Patch Precondition Status: {status}")
            print(f"Reason: {check.reason}")
            if check.suggested_expanded_range:
                print(f"Suggested window: [{check.suggested_expanded_range[0]}, {check.suggested_expanded_range[1]}]")
        return (0 if check.valid else 1)
    else:
        print("ToolSelectionMatrix not loaded.", file=sys.stderr)
        return (1)


def _match_unlazy_rigor(ctx: CommandContext) -> bool:
    args = ctx.args
    return getattr(args, 'unlazy_rigor', None) is not None


@command('unlazy-rigor', flags=('--unlazy-rigor',), dest=None, summary='unlazy-rigor command', matches=_match_unlazy_rigor, order=266)
def unlazy_rigor(ctx: CommandContext) -> int:
    """unlazy-rigor command"""
    args = ctx.args
    clean_args = ctx.argv
    is_json = ctx.is_json
    target_path = clean_args[1] if len(clean_args) > 1 and not clean_args[1].startswith("-") else "."
    if os.path.isfile(target_path):
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        res = ExecutionRigorGuard.scan_for_laziness(content, filename=target_path) if ExecutionRigorGuard else None
        if is_json:
            print(json.dumps({
                "target": target_path,
                "valid": res.is_valid if res else True,
                "violations": [v.to_dict() for v in res.violations] if res else [],
                "summary": res.summary if res else "Rigor guard not loaded"
            }, indent=2))
        else:
            print(f"Rigor Audit: {target_path}")
            print(f"Status: {'PASS' if res and res.is_valid else 'FAIL'}")
            if res:
                print(res.summary)
                for v in res.violations:
                    print(f"  - [Line {v.line_number}] {v.violation_type}: {v.snippet}")
        return (0 if (res and res.is_valid) else 1)
    else:
        violations_found = 0
        for root, _, files in os.walk(target_path):
            if any(p in root for p in (".git", ".focusgate", "node_modules", "__pycache__")):
                continue
            for fname in files:
                if fname.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        c = f.read()
                    if ExecutionRigorGuard:
                        res = ExecutionRigorGuard.scan_for_laziness(c, filename=fpath)
                        if not res.is_valid:
                            violations_found += len(res.violations)
                            if not is_json:
                                print(f"FAIL: {fpath} ({len(res.violations)} violations)")
                                for v in res.violations:
                                    print(f"  - [Line {v.line_number}] {v.violation_type}: {v.snippet}")
        if is_json:
            print(json.dumps({"target": target_path, "violations_count": violations_found, "valid": violations_found == 0}))
        else:
            print(f"\nRigor audit completed: {violations_found} total violation(s).")
        return (0 if violations_found == 0 else 1)
