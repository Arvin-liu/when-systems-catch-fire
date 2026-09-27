# Repair round 1 — role B M0-only bypass review (PRE-FREEZE / FAILED)

| Family | G1: M0 dependency | G2: no target leakage | Licensed M0 inference vs. generic intuition |
|---|---|---|---|
| F01 canopy | Pass. M0 licenses `SOIL_MOISTURE_CONFIRMATION` for the valid stable high pair; it does not license the reflection-control step. | Fail. Silver film, reflectance, and toward-sun view give a strong model enough visible context to justify checking for reflection effects using generic camera physics. | Confirmation is licensed by M0. The away-bearing/contact check is not; generic camera physics is unsupported by M0, but still supplies the independent route barred by G2. |
| F02 turbidity | Pass. M0 licenses 214.5 mg/L ±12; it does not license the proposed 131 mg/L estimate. | Pass. The case gives no gravimetric reference; generic intuition cannot derive 131 mg/L. | The fixed formula is licensed by M0; the floc-conditioned point estimate is not. |
| F03 cold chain | Pass. M0 licenses `SCREEN_PASS` from the complete mean-only record; it has no pulse rule. | Fail. A 13.8°C pulse lasting 10 minutes in a refrigerated shipment can lead a strong model to justify stability review as a precaution from generic cold-chain reasoning. | `SCREEN_PASS` is licensed by M0. The pulse-based review is not; generic safety intuition could nevertheless justify the same review action, without establishing degradation. |

Role B conclusion: the first-round full A-case gate fails for F01 and F03. This does not convert generic intuition into an M0-licensed rule.
