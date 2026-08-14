# map-maintainer-sustainability-economics

Observer: maintainer deciding what to keep, rent, automate, standardize, or fund

Decision question: Which costs and responsibilities must be retained, automated, rented, standardized, or covered by sponsorship?

Value recipient / affected subject: maintainer, noncommercial users, commercial users, and affected subjects

Claim ceiling: `derived_resource_navigation_view`

## Map

```mermaid
flowchart LR
  maintainer_judgment["Maintainer judgment and Charter responsibility<br/>GENESIS<br/>preserve"]
  ai_quota["AI quota and model access<br/>PRODUCT_RENTAL<br/>rent"]
  ci_compute["CI compute<br/>COMMODITY_UTILITY<br/>rent"]
  foundation_validators["Foundation validators<br/>CUSTOM_BUILT<br/>automate"]
  commercial_license["Commercial license and reciprocity path<br/>CUSTOM_BUILT<br/>standardize"]
  sponsorship["Sponsorship and sustainability funding<br/>GENESIS<br/>co_build"]
  storage_network["Storage, network, and repository hosting<br/>COMMODITY_UTILITY<br/>rent"]
  maintainer_judgment -->|control_flow| commercial_license
  sponsorship -->|value_flow| ai_quota
  sponsorship -->|value_flow| ci_compute
  ai_quota -->|information_flow| foundation_validators
  ci_compute -->|evidence_flow| foundation_validators
  storage_network -->|dependency| commercial_license
```

## Unmapped Residue

- residue-real-funding-response: Actual willingness of sponsors or commercial users to cover costs. (Requires real-world response beyond repository artifacts.)
