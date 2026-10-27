# Facet Contract: writing-fragments (v3.3)
Context: Writing | Mode: Unstructured Thought Ingestion | Eviction: On Gate Settle

```facet-meta
schema: 1
id: writing-fragments
summary: Append raw observations to the fragment store without structuring
priority: 5
mode: EPHEMERAL
applies_when: ["brain dump", "fragments", "raw thoughts", "fleeting", "unstructured", "notes on", "observations", "dump", "uncurated"]
socratic:
  grounding: ["CONTEXT.md"]
  stems: []
  cap: 0
usability:
  seed: "Append one unfiltered observation to .focusgate/FRAGMENTS.md."
  criterion: "FRAGMENTS.md grew; prior content byte-identical (DISK_SYNC honored)."
```

## Invariant Directives
1. DISK_SYNC: Read `.focusgate/FRAGMENTS.md` from disk before appending so human edits survive byte for byte.
2. FRAGMENT_STORE: Append each thought to `.focusgate/FRAGMENTS.md`, delimited by a line holding only `---`.
3. PURE_EXPLORE: Capture raw observations without ordering, headings or cleanup.
4. LEADING_WORDS: Keep the load-bearing technical metaphors verbatim so later drafting inherits them.

## Playbook
### Phases
1. Sync | DO: Read the current fragments file. | EXIT: byte length of the file recorded before the append.
2. Append | DO: Add the new fragment after a `---` line without touching earlier text. | EXIT: prior content is byte-identical and file size grew.
3. Mark the metaphors | DO: Underline the terms that carry the idea. | EXIT: count of key terms that are not verbatim substrings of the person's text is 0.
### Lazy Tells
- TIDY_UP | SAYS: "let me reorganize these while I am here" | DETECT: earlier fragments changed in the diff | INSTEAD: append only.
- STALE_BUFFER | SAYS: "I remember what the file holds" | DETECT: append made without a fresh read | INSTEAD: re-read from disk first.
### Gate Templates
```gate
- [ ] fragment-appended: the store holds at least 2 fragments
  CHECK: python3 -c "import sys; n=open('.focusgate/FRAGMENTS.md',encoding='utf-8').read().count('\n---\n'); sys.exit(0 if n>=1 else 1)" && echo FRAGMENTS_OK
  EXPECT: FRAGMENTS_OK
```
### Handoff
- NEXT: writing-shape | WHEN: enough fragments exist to propose a structure.
- NEXT: writing-beats | WHEN: the fragments form a story that needs ordering.
