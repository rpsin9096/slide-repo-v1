<!-- ARCHIVED. This document describes FocusGate v2.8 and is SUPERSEDED: v3.0 renamed most of these terms; the ubiquitous language is now in SPEC.md §2.
     Moved here by FocusGate v3.2 Loop 65 (AUDIT F18). Kept, not deleted, so the
     decision is on the record. Do not implement against it; read SPEC.md,
     ROADMAP.md and SKILL.md instead. -->

# FocusGate v2.8: Ubiquitous Language & Domain Model
## Deep Token Economy, Deterministic Tool Selection & Universal Anti-Cliché Verification Entities

**Domain Model Version:** 2.8.0  
**Context Purity:** Certified 100/100  

---

## 1. Core Ubiquitous Terms

### 1.1 Deep Token Economy Entities
- **TokenEconomyGovernor**: The consolidated deep module governing pre-dispatch inbound prompt sanitization, ephemeral session token ceilings (<1,500 tokens), dynamic test trace folding (<150 tokens), and global ROI token savings reporting.
- **FoldedOutput**: An immutable value object encapsulating folded test output, isolated root failure cause, auto-grep diagnostic snippet, and offloaded disk log reference.
- **InboundVerdict**: The sanitized prompt envelope produced by sliding window pruning, minified code stripping, and repetitive stack trace collapse.

### 1.2 Deterministic Tool Selection Entities
- **ToolSelectionMatrix**: The deterministic decision engine evaluating operational intent, target path state, and diff scope to select the correct tool on the first attempt (`write_to_file` vs `replace_file_content`).
- **PatchPreconditionCheck**: A pre-patch validation verification checking character-for-character whitespace matches, single-occurrence uniqueness, and line window bounds prior to patch execution.
- **PrePatchGuard**: The invariant guard preventing agent trial-and-error patch failures through pre-flight target inspection.

### 1.3 Intercommunication & Handoff Entities
- **EphemeralHandoffPacket**: An immutable, typed carrier value object binding source, target, upstream `GateReceipt`, bounded delta payload ($\le 100$ tokens), and SHA256 integrity checksum.
- **HandoffCoordinator**: The zero-copy in-memory dispatcher facilitating sub-millisecond ($<0.05$ms) inter-skill handoffs.
- **AntiCorruptionAdapter (ACL)**: The domain translation interface within each plugin translating foreign domain payloads into local execution parameters without conversational bloat.
- **DiagnosticAutoGrep**: The automatic error trace extractor in `FocusKernel` that retrieves a 3-line diagnostic window upon gate failure.

### 1.4 Ephemeral Context & Isolation Entities
- **EphemeralSession**: The isolated execution lifecycle boundary encapsulating sub-skill execution with clean prompt boundaries.
- **EphemeralSessionManager**: The lifecycle coordinator responsible for spawning sterile sessions and reaping working memory.
- **GateReceipt**: An immutable proof receipt capturing gate verification status, max 3 key findings, and cryptographic evidence hash strictly under 150 tokens.
- **EphemeralContextRetriever**: The on-demand search engine providing AST directive slicing, line-windowed source grepping, and mtime-aware local caching.
