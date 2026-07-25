# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R5-A Life Integrity Charter Candidate — governance/architecture overlay.

This package is a CANDIDATE overlay only. It encodes the user-authorized
anti-fragmentation and intervention-caution principle:

  "性命一体，身心互成。点火在认识、评价和干预人时，不得将人的生理、心理、
   行为、关系、环境与意义系统彼此割裂；任何局部优化，都必须接受完整生命、
   长期反馈、主体同意、风险边界与可逆性的共同检验。"

It does NOT activate a charter, does NOT enable human intervention, does NOT
authorize medical claims, does NOT start the Modern Wuzhen domain pack, does
NOT start a domain pack / federation runtime, and does NOT claim external
acceptance. Zhang Boduan and South-School materials remain historical and
conceptual sources and candidate protocols, never scientific or clinical
authority.

See docs/governance/life-integrity-charter-candidate-r1.md.
"""

from __future__ import annotations

from .registries import SCHEMA_VERSION, TASK_ID
from .manifest import CANDIDATE_MANIFEST, MANIFEST_REQUIRED_FLAGS, manifest_flags_consistent

__all__ = [
    "SCHEMA_VERSION",
    "TASK_ID",
    "CANDIDATE_MANIFEST",
    "MANIFEST_REQUIRED_FLAGS",
    "manifest_flags_consistent",
]
