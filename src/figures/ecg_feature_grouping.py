from __future__ import annotations


VALID_GROUPS = {
    "rate / rhythm",
    "interval",
    "duration",
    "axis",
    "amplitude",
    "morphology",
    "lead-specific measurement",
    "other",
}


def group_ecg_feature(feature_name: str) -> str:
    name = feature_name.lower()
    if any(term in name for term in ["rate", "rr", "hr", "rhythm"]):
        return "rate / rhythm"
    if any(term in name for term in ["int", "interval", "pq_", "pr_", "qt_"]):
        return "interval"
    if any(term in name for term in ["dur", "duration", "qrs_dur"]):
        return "duration"
    if "axis" in name:
        return "axis"
    if any(term in name for term in ["amp", "amplitude", "r_amp", "s_amp", "t_amp", "p_amp", "q_amp"]):
        return "amplitude"
    if any(term in name for term in ["morph", "shape"]):
        return "morphology"
    if any(f"_{lead}" in name for lead in ["i", "ii", "iii", "avr", "avl", "avf", "v1", "v2", "v3", "v4", "v5", "v6"]):
        return "lead-specific measurement"
    return "other"
