"""Deterministic task classifier and pipeline synthesizer (moved out of the CLI script in v3.3)."""
import os
import re
import sys
import json
from typing import Any, Dict, List, Optional, Tuple

class PipelineSynthesizer:
    """Classifies tasks and dynamically synthesizes multi-facet execution pipelines."""

    @staticmethod
    def _matched(ql: str) -> list:
        try:
            from core.facet_router import matched_ids
            return matched_ids(ql)
        except Exception:
            return []

    @staticmethod
    def synthesize(query: str, workspace_root: str = ".") -> Dict[str, Any]:
        ql = query.lower()
        from core.workspace_detector import WorkspaceDetector
        ws_info = WorkspaceDetector.detect(workspace_root)
        target_files = WorkspaceDetector.extract_target_files(query, workspace_root)
        primary_file = target_files[0] if target_files else None

        # P12: Bespoke Frontend Design & Implementation
        if "frontend-design" in PipelineSynthesizer._matched(ql) or "frontend-design" in ql:
            archetype = "FRONTEND_BESPOKE"
            pipeline_name = "Bespoke Frontend Design & Implementation"
            stages = [
                {"facet": "frontend-design", "description": "Anchor visual identity in subject matter and compile 2-pass anti-cliché design plan"},
                {"facet": "design-tokens", "description": "Extract bespoke 3-layer tokens, type roles, and verified palette"},
                {"facet": "prototype", "description": "Scaffold disposable HTML/CSS sandbox spike to validate layout & typography"},
                {"facet": "codebase-design", "description": "Establish clean component seam and props interface contract"},
                {"facet": "unlazy", "description": "Implement production component across 4-pass completion loop"},
                {"facet": "code-review", "description": "Execute dual-axis review and anti-cliché design oracle validation"}
            ]
            est_minutes = 30
            seed_step = {
                "action": "Draft subject grounding and 2-pass bespoke design plan in .focusgate/DESIGN-SPEC.md",
                "check": "git status",
                "expect": "On branch"
            }
        # P11: Design Audit & Accessibility Polish
        elif "focus-design" in PipelineSynthesizer._matched(ql):
            archetype = "DESIGN_AUDIT"
            pipeline_name = "Design Audit & Accessibility Polish"
            stages = [
                {"facet": "diagnosing-bugs", "description": "Run token and contrast audits to identify hardcoded styling and accessibility violations"},
                {"facet": "focus-design", "description": "Resolve design tokens and replacement accessible palettes"},
                {"facet": "unlazy", "description": "Refactor source code to use tokens and verified accessible colors"},
                {"facet": "code-review", "description": "Re-run automated oracles to ensure clean audit verdicts"}
            ]
            est_minutes = 20
            seed_step = {
                "action": "Run initial contrast and token audit across target source files",
                "check": "git status",
                "expect": "On branch"
            }
        # P9: UI Component Slicing
        elif any(k in ql for k in ("ui component", "design system", "design tokens", "button component", "card layout", "card component", "modal dialog", "table ui", "navigation bar", "styling", "css variables", "shadcn", "tailwind", "alert banner")):
            archetype = "UI_COMPONENT"
            pipeline_name = "UI Component & Design System Slicing"
            stages = [
                {"facet": "writing-fragments", "description": "Capture component states, props, and design requirements"},
                {"facet": "focus-design", "description": "Define token mappings, 3-layer CSS variables, and layout specs"},
                {"facet": "prototype", "description": "Scaffold throwaway HTML/CSS spike to test layout and responsive behavior"},
                {"facet": "codebase-design", "description": "Establish public component seam and props interface"},
                {"facet": "unlazy", "description": "Implement production component with automated token and contrast acceptance gates"}
            ]
            est_minutes = 35
            seed_step = {
                "action": "Draft UI component specifications and token requirements in .focusgate/DESIGN-SPEC.md",
                "check": "git status",
                "expect": "On branch"
            }
        # P10: Visual Design & Creative Asset Production
        elif "banner-safe-zone" in PipelineSynthesizer._matched(ql) or "logo" in ql:
            archetype = "VISUAL_ASSET"
            pipeline_name = "Visual Design & Creative Asset Production"
            stages = [
                {"facet": "triage", "description": "Determine target platform dimensions and brand requirements"},
                {"facet": "focus-design", "description": "Select art direction, verify safe-zone bounds, and extract palette"},
                {"facet": "prototype", "description": "Generate multi-format HTML canvas or SVG preview"},
                {"facet": "code-review", "description": "Execute automated safe-zone oracle and WCAG contrast verifications"}
            ]
            est_minutes = 20
            seed_step = {
                "action": "Select visual art direction and confirm target platform safe-zone specs",
                "check": "git status",
                "expect": "On branch"
            }
        # P8: Narrative Postmortem
        elif any(k in ql for k in ("post-mortem", "postmortem", "incident", "tutorial", "migration guide", "release notes", "changelog")):
            archetype = "POSTMORTEM"
            pipeline_name = "Narrative Guide & Post-Mortem"
            stages = [
                {"facet": "diagnosing-bugs", "description": "Gather chronological investigation events and settled defect gate"},
                {"facet": "writing-beats", "description": "Structure beat-by-beat narrative exposition (symptom -> cause -> prevention)"},
                {"facet": "code-review", "description": "Verify narrative accuracy against actual code diff and tracer tests"}
            ]
            est_minutes = 25
            seed_step = {
                "action": "Propose starting beat establishing incident prerequisites",
                "check": "git status",
                "expect": "On branch"
            }
        # P4: Loop Synthesis / Automation
        elif "loop-me" in PipelineSynthesizer._matched(ql):
            archetype = "AUTOMATION"
            pipeline_name = "Loop Synthesis"
            stages = [
                {"facet": "loop-me", "description": "Identify recurring loop and establish Push Right checkpoint doctrine"},
                {"facet": "grilling", "description": "Stress-test failure modes, fallbacks, and human-in-the-loop triggers"},
                {"facet": "unlazy", "description": "Compile workflow spec into deterministic execution runners and gates"}
            ]
            est_minutes = 25
            seed_step = {
                "action": "Draft 1-paragraph workflow trigger and push-right checkpoint",
                "check": "git status",
                "expect": "On branch"
            }
        # P7: Architectural RFC Spec
        elif "writing-shape" in PipelineSynthesizer._matched(ql):
            archetype = "SPECIFICATION"
            pipeline_name = "Architectural RFC Spec"
            stages = [
                {"facet": "writing-fragments", "description": "Mine architectural constraints, invariants, and latency goals"},
                {"facet": "codebase-design", "description": "Define deep module interface and verify 2-adapter justification"},
                {"facet": "writing-shape", "description": "Compile formal RFC with prerequisite concept grounding"},
                {"facet": "prototype", "description": "Scaffold interactive HTML logic spike to validate state machine"}
            ]
            est_minutes = 45
            seed_step = {
                "action": "Draft 1-paragraph problem statement and candidate public seam",
                "check": "git status",
                "expect": "On branch"
            }
        # P6: Ideation to Execution
        elif "writing-fragments" in PipelineSynthesizer._matched(ql) or "spark" in ql:
            archetype = "IDEATION"
            pipeline_name = "Ideation to Implementation"
            stages = [
                {"facet": "writing-fragments", "description": "Mine raw thoughts and identify load-bearing leading words"},
                {"facet": "writing-shape", "description": "Ground prerequisite concepts and shape fragments into a structured spec"},
                {"facet": "writing-for-agents", "description": "Compile execution slices into subagent brief with checkable criteria"},
                {"facet": "unlazy", "description": "Implement vertical slices test-first against tracer gates"}
            ]
            est_minutes = 30
            seed_step = {
                "action": "Append initial raw thought to .focusgate/FRAGMENTS.md",
                "check": "echo FRAGMENT_OK",
                "expect": "FRAGMENT_OK"
            }
        # P5: Atomic Sprint (Micro-tasks)
        elif any(k in ql for k in ("typo", "bump version", "badge link", "single comment", "change default timeout", "quick 2-minute", "atomic")):
            archetype = "ATOMIC"
            pipeline_name = "Atomic Sprint"
            stages = [
                {"facet": "unlazy", "description": "Scaffold 2-minute activation seed gate"},
                {"facet": "unlazy", "description": "Execute implementation against tracer check"},
                {"facet": "code-review", "description": "Verify code changes against repo standards"}
            ]
            est_minutes = 10
            seed_step = {
                "action": f"Execute atomic micro-step: {query}",
                "check": "git status",
                "expect": "On branch"
            }
        # P1: Rapid Defect Resolution
        elif "diagnosing-bugs" in PipelineSynthesizer._matched(ql):
            archetype = "DEFECT"
            pipeline_name = "Rapid Defect Resolution"
            stages = [
                {"facet": "triage", "description": "Verify and reproduce defect locally"},
                {"facet": "diagnosing-bugs", "description": "Isolate minimal failing reproduction command"},
                {"facet": "unlazy", "description": "Implement minimal fix against failing tracer gate"},
                {"facet": "code-review", "description": "Dual-axis verification (Standards + Spec) to prevent regression"}
            ]
            est_minutes = 15
            if primary_file and ws_info["stack"] == "python":
                file_stem = os.path.splitext(os.path.basename(primary_file))[0]
                action_text = f"Reproduce failure locally in {primary_file}: {query}"
                check_cmd = f"pytest -k {file_stem} || python3 -m unittest"
            elif primary_file and ws_info["stack"] == "typescript_node":
                action_text = f"Reproduce failure locally in {primary_file}: {query}"
                check_cmd = f"npm test -- {primary_file}"
            elif ws_info["test_runner"] != "git status":
                action_text = f"Reproduce failure locally: {query}"
                check_cmd = ws_info["test_runner"]
            else:
                action_text = f"Reproduce failure locally: {query}"
                check_cmd = "pytest || npm test || echo 'reproduce'"

            seed_step = {
                "action": action_text,
                "check": check_cmd,
                "expect": "FAIL"
            }
        # P2: Strategic Wayfinding
        elif "wayfinder" in PipelineSynthesizer._matched(ql) or any(k in ql for k in ("fog", "maybe", "concept")):
            archetype = "STRATEGY"
            pipeline_name = "Strategic Wayfinding"
            stages = [
                {"facet": "grilling", "description": "Socratic interview to sharpen ambiguity into concrete options"},
                {"facet": "wayfinder", "description": "Chart shared map and frontier decision tickets on issue tracker"},
                {"facet": "prototype", "description": "Scaffold disposable interactive HTML/UI spike to validate design"},
                {"facet": "unlazy", "description": "Decompose unblocked frontier into deterministic acceptance gates"}
            ]
            est_minutes = 45
            seed_step = {
                "action": "Answer the primary open question with one recommended choice",
                "check": "git status",
                "expect": "On branch"
            }
        # P3: Deep Module Redesign
        elif "codebase-design" in PipelineSynthesizer._matched(ql):
            archetype = "ARCHITECTURE"
            pipeline_name = "Deep Module Redesign"
            stages = [
                {"facet": "codebase-design", "description": "Define deep module interface and identify clean public seams"},
                {"facet": "prototype", "description": "Build disposable logic harness to test concurrency/state machine"},
                {"facet": "unlazy", "description": "Execute vertical slices test-first through the public seam"},
                {"facet": "code-review", "description": "Audit depth, adapter discipline, and test surface integrity"}
            ]
            est_minutes = 40
            seed_step = {
                "action": "Inspect public interface boundary of target module",
                "check": "git status",
                "expect": "On branch"
            }
        else:
            archetype = "ATOMIC"
            pipeline_name = "Atomic Sprint"
            stages = [
                {"facet": "unlazy", "description": "Scaffold 2-minute activation seed gate"},
                {"facet": "unlazy", "description": "Execute implementation against tracer check"},
                {"facet": "code-review", "description": "Verify code changes against repo standards"}
            ]
            est_minutes = 10
            action_text = f"Execute atomic micro-step in {primary_file}: {query}" if primary_file else f"Execute atomic micro-step: {query}"
            seed_step = {
                "action": action_text,
                "check": ws_info["test_runner"] if ws_info["stack"] != "generic" else "git status",
                "expect": "On branch" if ws_info["stack"] == "generic" else ""
            }

        from core.gates.evidence import falsifiable_seed
        _c, _e, _a = falsifiable_seed(seed_step["check"], seed_step["expect"], seed_step["action"])
        seed_step = {"action": _a, "check": _c, "expect": _e}

        return {
            "query": query,
            "archetype": archetype,
            "pipeline": pipeline_name,
            "stages": stages,
            "est_minutes": est_minutes,
            "seed_step": seed_step,
            "workspace_stack": ws_info["stack"],
            "target_files": target_files
        }
