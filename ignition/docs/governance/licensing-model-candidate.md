# Licensing Model Candidate

Status: candidate decision record. This is not legal advice and does not change the root `LICENSE`.

## Decision Direction

Point Fire / When Systems Catch Fire should move toward a publicly auditable, layered, commercially reciprocal, delayed-open model for future versions. The project should not describe future BUSL-covered core implementation as OSI open source. The accurate term is source-available until the conversion date.

## Options Compared

| Model | Strength | Risk |
| --- | --- | --- |
| MIT | Maximizes reuse and OSI compatibility | Allows free commercial extraction and leaves maintenance, AI/API, compute, and living costs externalized to the maintainer |
| AGPL-3.0-or-later | Strong copyleft for networked use and OSI/free-software alignment | May still permit uncompensated commercial use if obligations are satisfied; can deter some integrations |
| BUSL-1.1 | Permits public source, modification, redistribution, and broad non-production use while reserving commercial production use | Not OSI open source; requires careful Additional Use Grant and conversion license drafting |
| CC BY-NC-SA 4.0 | Fits original research documents and non-commercial sharing | Not for software; “NonCommercial” can be ambiguous and is not OSI open source |
| Open core | Keeps interfaces broad while protecting high-cost implementation | Boundary disputes if core/edge split is unclear |
| Dual or layered licensing | Lets education/public-interest use stay easy while commercial users share cost | Requires contributor rights mechanism and ongoing governance discipline |

## Candidate Model

1. Core executable software: BUSL-1.1 candidate. Additional Use Grant covers personal learning, education, academic work, non-commercial research, evaluation, and public-benefit nonprofit use. Commercial production use requires a separate commercial license or written reciprocal agreement.
2. Change license: each version converts no later than four years after first public release to AGPL-3.0-or-later.
3. Original research documents, reports, and curated data: CC BY-NC-SA 4.0 candidate.
4. Value charter, public interface specifications, and interoperability schema: evaluate CC BY-SA 4.0 or Apache-2.0 so principles and interfaces can spread widely.
5. Third-party material: original rights remain with their owners; do not relicense.
6. Names, marks, and endorsement: reserve official identity and trademark-like use regardless of code/content license.

## Rationale

The project’s value charter rejects systems where one local actor captures benefits while another subject continuously bears the cost. Maintenance time, basic living needs, AI/API quotas, compute, equipment, network, review, and governance work are legitimate infrastructure costs. Commercial users who gain revenue or production advantage from the project should help sustain the project.

## Non-Effect and Pending Review

This document does not replace the root MIT `LICENSE`, does not revoke existing MIT grants, does not create a commercial license by itself, and does not claim professional legal review. Effective migration requires maintainer approval, release-boundary marking, contributor-license mechanism, and legal review.
