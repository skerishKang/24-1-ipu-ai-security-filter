"""B63 R0 annotation taxonomy v0.1.

Single source of truth for PHI labels, classes, risk tiers, and clinical
utility types. The JSON schema in benchmark/schemas mirrors these constants.
"""

from __future__ import annotations

CORPUS_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1.0"
CORPUS_SEED = 20260825

DIRECT_LABELS = frozenset(
    {
        "PATIENT_NAME",
        "GUARDIAN_NAME",
        "PHONE",
        "EMAIL",
        "ADDRESS",
        "RRN",
        "FOREIGN_REG_NUMBER",
        "MRN",
        "INSURANCE_NUMBER",
        "CLINICIAN_NAME",
        "CLINICIAN_ID",
    }
)

CONTEXTUAL_LABELS = frozenset(
    {
        "HOSPITAL_NAME",
        "WARD_DEPARTMENT",
        "ORDER_ID",
        "EXACT_TIMESTAMP",
    }
)

QUASI_LABELS = frozenset(
    {
        "AGE",
        "SEX",
        "RARE_DISEASE",
        "RARE_PROCEDURE",
        "DETAILED_REGION",
        "OCCUPATION",
        "ADMIT_DISCHARGE_DATE",
        "UNIQUE_EVENT",
    }
)

ALL_PHI_LABELS = DIRECT_LABELS | CONTEXTUAL_LABELS | QUASI_LABELS

HIGH_RISK_LABELS = DIRECT_LABELS

DIRECT_CLASS = "direct"
CONTEXTUAL_CLASS = "contextual"
QUASI_CLASS = "quasi"

LABEL_CLASS: dict[str, str] = {label: DIRECT_CLASS for label in DIRECT_LABELS}
LABEL_CLASS.update({label: CONTEXTUAL_CLASS for label in CONTEXTUAL_LABELS})
LABEL_CLASS.update({label: QUASI_CLASS for label in QUASI_LABELS})

RISK_TIER_HIGH = "high"
RISK_TIER_STANDARD = "standard"


def risk_tier_for(label: str) -> str:
    return RISK_TIER_HIGH if label in HIGH_RISK_LABELS else RISK_TIER_STANDARD


UTILITY_TYPES = (
    "medication",
    "dosage",
    "frequency_route",
    "lab_value",
    "diagnosis",
    "procedure",
    "symptom",
    "negation_cue",
    "uncertainty_cue",
    "temporality",
    "event_order_marker",
)

SUBSETS = (
    "direct",
    "institutional",
    "quasi",
    "negative",
    "utility",
)

# Quasi categories that count toward combination risk when co-present.
COMBO_CAPABLE_QUASI = QUASI_LABELS - {"AGE", "SEX"}
