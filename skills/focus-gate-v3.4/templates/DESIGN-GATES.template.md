# FocusDesign Ledger: {task_name}
State: [Step 1 of 4] [0/2 gates met] [Est: 20 min]

## 1. Domain Anchors (Micro-Glossary)
- **{canonical_term}**: {term_definition}
  _Avoid_: {term_avoid}
- **DesignTokens**: 3-layer variables (primitive -> semantic -> component) stored in assets/design-tokens.css.
  _Avoid_: HardcodedHex, ArbitraryPixelSpacing

## 2. Acceptance Gates

### Spikes (Throwaway Explorations)
- [ ] spike-ui-{spike_name}: Test responsive layout and color harmony
  BRANCH: ui
  QUESTION: Does the proposed palette meet WCAG AA 4.5:1 contrast across light and dark modes?
  ARTIFACT: .focusdesign/prototypes/{spike_name}.html
  CHECK: python3 {cli_path} --verify-spike .focusdesign/prototypes/{spike_name}.html
  EXPECT: VALID_DESIGN_PROTOTYPE

### Production Gates
- [ ] gate-1-token-compliance: All template styles reference valid CSS tokens
  CHECK: python3 {cli_path} --audit-tokens {target_file}
  EXPECT: AUDIT_TOKENS_PASS

- [ ] gate-2-contrast-verification: Primary CTA meets WCAG AA contrast threshold (>= 4.5:1)
  CHECK: python3 {cli_path} --audit-contrast "{fg_color}" "{bg_color}"
  EXPECT: CONTRAST_PASS_AA

## 3. Micro-ADR Ledger
- **None yet.**
