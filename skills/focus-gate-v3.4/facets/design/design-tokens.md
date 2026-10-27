# Facet Contract: design-tokens (v3.3)
Context: Design | Mode: 3-Layer Token Governance | Eviction: On Gate Settle

```facet-meta
schema: 1
id: design-tokens
summary: 3-layer token governance primitive to semantic to component
priority: 6
mode: WINDOW
applies_when: ["design tokens", "css variables", "theme", "palette", "3-layer", "primitive semantic", "tailwind config", "shadcn", "design system", "styling"]
oracle: ["--sync-tokens", "--audit-tokens"]
socratic:
  grounding: ["CONTEXT.md", "file:line"]
  stems: ["Which semantic layer owns this token - cite the primitive it aliases."]
  cap: 1
usability:
  seed: "Run --audit-tokens on one stylesheet and fix the first hardcoded hex."
  criterion: "--audit-tokens reports zero hardcoded hex/rgb in touched files."
```

## Invariant Directives
1. LAYER_MODEL: Use 3 tiers: primitive (`--color-blue-600: #2563eb`), semantic (`--color-primary: var(--color-blue-600)`), component (`--button-bg: var(--color-primary)`).
2. ALLOWLIST_AUDIT: Reject hardcoded hex, rgb and font names in source with `focus-gate.py --audit-tokens <path>`.
3. SYNC_ORACLE: Generate tokens from the brand file with `--sync-tokens <brand_md> --out <dir>` instead of typing them twice.
4. THEME_ISOLATION: Scope dark mode and brand overrides to semantic-layer variables only, never to primitives or components.

## Playbook
### Phases
1. Inventory raw values | DO: Run `--audit-tokens` on the touched stylesheets. | EXIT: violation list with `line N: [hardcoded-hex]` entries and a total count.
2. Define the layers | DO: Name primitives, then semantic aliases, then component aliases. | EXIT: every semantic token resolves with `var(--primitive)`.
3. Replace | DO: Swap each raw value for its component or semantic token. | EXIT: `--audit-tokens` prints `AUDIT_TOKENS_PASS`.
4. Isolate themes | DO: Override only semantic tokens inside the theme selector. | EXIT: zero primitive tokens redefined inside a theme block.
### Lazy Tells
- RAW_HEX_SNEAKS_BACK | SAYS: "one hex is fine here" | DETECT: `--audit-tokens` reports `[hardcoded-hex]` | INSTEAD: add or reuse a semantic token.
- FLAT_TOKENS | SAYS: "one layer of variables is enough" | DETECT: components reference primitives directly | INSTEAD: route through a semantic alias.
### Gate Templates
```gate
- [ ] no-raw-colors: touched stylesheets use tokens only
  CHECK: python3 scripts/focus-gate.py --audit-tokens {path}
  EXPECT: AUDIT_TOKENS_PASS
```
### Handoff
- NEXT: focus-design | WHEN: tokens resolve and contrast must be proven.
- NEXT: ui-ux-pro-max | WHEN: components still lack declared interaction states.
