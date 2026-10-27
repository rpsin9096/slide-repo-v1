# RFC: {title}

**Status:** Draft  
**Author:** {author}  
**Target Module:** `{module_path}`  

## 1. Grounded Concepts & Prerequisites
- **{prerequisite_concept}**: {concept_definition}

## 2. Problem Statement & Motivation
{problem_description}

## 3. Proposed Architecture & Seams
- **Public Seam**: `{public_seam_signature}`
- **Adapters Justified**:
  1. *Production Adapter*: `{prod_adapter}`
  2. *Testing Fake Adapter*: `{test_adapter}`

## 4. Verification Tracer Criteria
- [ ] gate-01: {acceptance_criteria}
  CHECK: {verification_command}
  EXPECT: {expected_token}
