"""H_TI_core window comparability classification (effective formula fingerprint)."""

from __future__ import annotations

from typing import Any

HTI_COMPARABILITY_CLASSES: tuple[str, ...] = (
    "full_4_component",
    "no_technique",
    "no_register",
    "instrument_family_only",
    "no_active_events",
    "partial_other",
)


def classify_hti_comparability_class(
    *,
    feats: dict[str, Any] | None,
    active_weights: dict[str, float] | None,
) -> str:
    """
    Label which H_TI_core components were active for one window.

    Used to warn when comparing ``H_TI_core`` values computed with different effective
    weighted geometric means (renormalised active weights).
    """
    if feats is None:
        return "no_active_events"
    aw = active_weights or {}
    if not aw:
        return "no_active_events"

    has_tech = "technique_uniformity" in aw
    has_reg = "register_proximity" in aw
    has_instr = "instrument_uniformity" in aw
    has_fam = "family_uniformity" in aw

    if has_instr and has_fam and has_tech and has_reg:
        return "full_4_component"
    if has_instr and has_fam and not has_tech and not has_reg:
        return "instrument_family_only"
    if has_instr and has_fam and not has_tech and has_reg:
        return "no_technique"
    if has_instr and has_fam and has_tech and not has_reg:
        return "no_register"
    return "partial_other"
