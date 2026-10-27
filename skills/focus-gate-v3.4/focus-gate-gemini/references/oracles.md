# FocusGate v3.4 Cognitive Verification Oracles

Seven deterministic oracles implemented as cognitive and structural self-auditing rules for Gemini Spark and Gemini Chat.

---

## 1. Prose Cliché Oracle
Detects and purges generic AI writing tells from technical documents and conversational responses:
- **Throat-Clearing Preambles**: Banned opening fluff ("Certainly!", "Sure! I would be happy to help", "In today's fast-paced digital landscape").
- **AI Buzzwords**: Banned corporate/AI flourish words ("delve", "testament to", "rich tapestry", "ever-evolving", "pivotal role", "paramount importance", "seamlessly integrate", "foster collaboration").
- **Sycophancy**: Banned ego-stroking directives ("You are a world-class engineer...", "Think carefully and do your best").
- **Faux-Summaries**: Banned closing summary boilerplate ("In conclusion", "To summarize", "In summary").

---

## 2. Code Cliché Oracle
Audits source code across languages to eliminate shallow AI architectures:
- **Junk-Drawer Modules**: Files named `utils.py`, `helpers.py`, `common.ts`, `misc.py` with loose functions are rejected. Split logic into cohesive, domain-named modules.
- **Shotgun Exception Handling & Swallowed Exceptions**: Reject broad `except: pass`, `except Exception: ...`, or empty `catch (err) {}`. Require specific caught types and explicit handling or re-raising.
- **Anemic Passthroughs**: Reject stateless single-method wrapper classes that merely forward calls without value-add.
- **Two-Adapter Requirement**: Any core architectural interface must be justified and exercised by at least two concrete adapters (e.g. Production + Test/Fake).
- **Type Dilution**: Ban TypeScript `as any` and Rust `.unwrap()` sprees.

---

## 3. Design Cliché Oracle & Visual Governance
Eliminates stereotypical AI visual patterns:
- **Gradient Hero Clichés**: Avoid generic indigo-to-purple background gradients. Ground palettes in concrete brand identity.
- **Uniform Card Grids**: Avoid identical card grids without visual hierarchy.
- **State Completeness**: Every button, input, and interactive link must specify:
  - Default state
  - Hover state (`:hover`)
  - Focus-visible state (`:focus-visible` with high-contrast outline)
  - Active state (`:active`)
  - Disabled state (`:disabled` or `aria-disabled="true"`)
  - Loading state (if asynchronous)

---

## 4. Contrast Oracle (WCAG 2.1 AA)
Calculates exact relative luminance and evaluates accessibility conformance:
- Channel Linearization ($C \in \{R, G, B\} \in [0.0, 1.0]$):
  - If $C \le 0.04045 \implies c = C / 12.92$
  - Else $c = ((C + 0.055) / 1.055)^{2.4}$
- Relative Luminance: $L = 0.2126 r + 0.7152 g + 0.0722 b$.
- Contrast Ratio: $\text{Ratio} = (L_1 + 0.05) / (L_2 + 0.05)$ where $L_1 > L_2$.
- Thresholds:
  - Normal Text: $\ge 4.5:1$ (AA), $\ge 7.0:1$ (AAA).
  - Large Text ($\ge 18\text{pt}$ or $\ge 14\text{pt}$ bold): $\ge 3.0:1$ (AA), $\ge 4.5:1$ (AAA).

---

## 5. Safe-Zone Oracle
Validates that critical visual branding, logos, and typography reside inside the **central 70% rectangular envelope** (15% margin on all 4 edges):
$$\text{Safe Boundary: } [0.15 W, 0.15 H] \text{ to } [0.85 W, 0.85 H]$$
Platforms validated:
- 16:9 Landscape (`16x9`)
- 9:16 Portrait (`9x16`)
- 1:1 Square (`1x1`)
- 4:5 Social (`4x5`)
- 3:2 Banner (`3x2`)

---

## 6. Context Sufficiency Oracle
Guards subagent briefs and multi-agent handoffs against context starvation:
- `BARE_POINTER`: Upstream dependency is supplied as a naked `@hash` or file path without explanation.
- `LOST_SUMMARY`: Upstream receipt carries empty summaries or placeholder text.
- Mandatory Brief Contents: Clear objective, boundary interfaces, architectural invariants, checkable exit criteria, and timeout limits.

---

## 7. Infinite Loop & CPU Safety Guardian
Statically analyzes loops and recursion:
- Identifies unbounded `while True:` without internal breaks, returns, or sleep intervals.
- Checks that recursive functions contain unambiguous base cases.
- Injects defensive iteration counter caps into open-ended event polling loops.
- Flags swallowed exceptions in loops that could trigger infinite error cascades.
