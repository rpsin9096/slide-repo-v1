# Design Specification: {feature_name}

**Status:** Draft  
**Target Module / Component:** `{component_path}`  
**Primary Platform:** `{platform}` (Aspect: `{aspect_ratio}`)  

## 1. Grounded Design Tokens & Palette
- **Primary Color**: `{primary_color_hex}` (WCAG AA ratio on background: `{contrast_ratio}:1`)
- **Background / Surface**: `{surface_color_hex}`
- **Typography Scale**: Heading `{heading_font}` / Body `{body_font}`

## 2. Component Hierarchy & Layout
- **Visual Container**: `{container_dimensions}`
- **Safe-Zone Bounds**: `{safe_zone_box}` (Central 70%)
- **Interactive Elements**:
  1. Primary Button (`{primary_btn_state}`)
  2. Input / Control (`{control_state}`)

## 3. Observable Acceptance Gates
- [ ] gate-design-01: Audit token references in `{component_path}`
  CHECK: python3 {cli_path} --audit-tokens {component_path}
  EXPECT: AUDIT_TOKENS_PASS

- [ ] gate-design-02: Verify WCAG AA contrast for text on background
  CHECK: python3 {cli_path} --audit-contrast "{primary_color_hex}" "{surface_color_hex}"
  EXPECT: CONTRAST_PASS_AA

- [ ] gate-design-03: Verify layout safe-zone compliance
  CHECK: python3 {cli_path} --audit-safe-zone {dimensions} --platform {platform} --box {safe_zone_box}
  EXPECT: SAFE_ZONE_PASS
