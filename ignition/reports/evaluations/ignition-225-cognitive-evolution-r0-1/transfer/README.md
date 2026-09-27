# Transfer phase design

This directory freezes the neutral transfer prompt, response schema, task template, condition-map schema, and sealed target index. Trial manifests and condition map are instantiated only after all six revision tasks terminate and mechanically usable M1 artifacts are known.

The transfer condition map and sealed targets must never enter successor transfer inputs. Successor-visible trial manifests contain opaque IDs and file references only; no condition label, target, evaluator criterion, or disposition threshold.
