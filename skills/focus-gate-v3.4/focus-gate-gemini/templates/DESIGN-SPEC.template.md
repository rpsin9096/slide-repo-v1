# Design Specification: {feature_or_system_name}

## 1. Domain Grounding & Aesthetic Identity
- **Subject Matter**: {core_subject_and_emotional_tone}
- **Anti-Cliché Palette**: {grounded_color_choices_not_generic_purple}

## 2. 3-Layer Design Tokens
### Primitive Tokens
- `--color-primary-raw`: `{primary_hex}`
- `--color-accent-raw`: `{accent_hex}`

### Semantic Tokens
- `--color-brand`: `var(--color-primary-raw)`
- `--color-action`: `var(--color-accent-raw)`

### Component Tokens
- `--btn-primary-bg`: `var(--color-brand)`
- `--btn-primary-text`: `#ffffff`

## 3. Safe-Zone & Viewport Constraints
- Target platform: {aspect_ratio} (Central 70% safe zone enforced).
