# Brand Guidelines (Starter)

> Fill this in, then run `--sync-tokens` to generate the 3-layer token files.
> Keep every color as a `#RRGGBB` hex so the synchronizer can extract it.

## Identity

- **Brand name**: Acme
- **Voice**: Plain, direct, confident. Short sentences. No jargon.
- **Primary brand color**: `#2563EB` (trust, action)
- **Accent brand color**: `#10B981` (success, growth)

## Typography

- **Headings**: system-ui stack, weight 700, tight leading
- **Body**: system-ui stack, weight 400, 1.5 line height
- Never ship a hardcoded `font-family` in components; reference
  `var(--font-family-heading)` / `var(--font-family-body)` instead.

## Rules

1. All component colors reference `assets/design-tokens.css` variables.
2. Text contrast must meet WCAG AA (4.5:1 normal, 3:1 large).
3. Banner copy stays inside the central 70% safe zone.
