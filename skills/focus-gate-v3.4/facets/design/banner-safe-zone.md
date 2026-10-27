# Facet Contract: banner-safe-zone (v3.3)
Context: Design | Mode: Viewport & Safe-Zone Validation | Eviction: On Gate Settle

```facet-meta
schema: 1
id: banner-safe-zone
summary: Central 70 percent safe-zone validation for banner and hero formats
priority: 6
mode: WINDOW
applies_when: ["banner", "hero", "16:9", "9x16", "social post", "display ad", "slide", "deck", "safe-zone", "crop", "presentation", "creative asset", "safe box"]
oracle: ["--audit-safe-zone"]
socratic:
  grounding: ["active gate contract", "file:line"]
  stems: ["Which preset aspect owns {file}?"]
  cap: 1
usability:
  seed: "Run --audit-safe-zone on one banner svg at 16x9."
  criterion: "Audit exits 0 with all critical copy inside the 70 percent box."
```

## Invariant Directives
1. 70PCT_ENVELOPE: Place critical copy, CTAs and brand marks inside the central 70 percent box of every target canvas.
2. VALIDATION_ORACLE: Prove layout with `focus-gate.py --audit-safe-zone <WxH or svg> --platform <p>` and quote its verdict, never an eyeball estimate.
3. PRESET_ASPECTS: Validate each delivery format separately against landscape-16x9, portrait-9x16, square-1x1, portrait-4x5 and landscape-3x2.
4. CROP_TOLERANCE: Keep only background in the outer 30 percent so any platform crop loses decoration, not meaning.

## Playbook
### Phases
1. Inventory formats | DO: List every target aspect and the platform that crops it. | EXIT: one line per format naming platform and aspect, count equals the deliverables.
2. Place content | DO: Position copy, CTA and logo using the 70 percent box of each aspect. | EXIT: each element has `x,y,w,h` fully inside its box.
3. Audit each format | DO: Run `--audit-safe-zone` once per aspect. | EXIT: every run prints `SAFE_ZONE_PASS`.
4. Clip test | DO: Crop 15 percent off every edge and reread the asset. | EXIT: message and CTA still readable and zero elements touch the cut.
### Lazy Tells
- ONE_FORMAT_ONLY | SAYS: "16x9 passes so the other formats will too" | DETECT: audit runs recorded are fewer than the inventory | INSTEAD: run one audit per aspect.
- EYEBALL_CENTER | SAYS: "it looks centered to me" | DETECT: no `SAFE_ZONE_PASS` line in the evidence | INSTEAD: run the oracle and keep its verdict.
### Gate Templates
```gate
- [ ] safe-16x9: launch banner copy stays inside the 70 percent box
  CHECK: python3 scripts/focus-gate.py --audit-safe-zone {spec} --platform landscape-16x9
  EXPECT: SAFE_ZONE_PASS
```
### Handoff
- NEXT: focus-design | WHEN: layout passes and contrast or token audits remain.
- NEXT: code-review | WHEN: every format has a `SAFE_ZONE_PASS` and the asset is ready to merge.
