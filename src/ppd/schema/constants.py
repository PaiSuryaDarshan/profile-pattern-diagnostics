"""
PPD constants.

This file defines the fixed assumptions of Profile Pattern Diagnostics (PPD).
Changing values here changes the meaning of all outputs.
"""

from dataclasses import dataclass

from typing import Optional

# ------------------------------------------------------------------
# Identity / versioning
# ------------------------------------------------------------------

PPD_NAME = "Profile Pattern Diagnostics (PPD)"
PPD_VERSION = "0.1.0-spec"


# ------------------------------------------------------------------
# Score scale semantics
# Raw scores are assumed to be on a 0–5 rubric scale and are
# linearly mapped to [0, 1].
# ------------------------------------------------------------------

RAW_SCORE_MIN = 0.0
RAW_SCORE_MAX = 5.0

NORMALIZED_MIN = 0.0
NORMALIZED_MAX = 1.0

NORMALIZATION_RULE = "linear_divide_by_5"  # x_norm = x / 5


# ------------------------------------------------------------------
# Dimension ordering
# Used ONLY for order-aware adjacency descriptor D.
# Leave empty until the semantic axis order is locked.
# ------------------------------------------------------------------

DIMENSION_ORDER = ()


# ------------------------------------------------------------------
# Thresholds (pattern gates / flags)
# The PDF defines the rules but not the numeric values.
# These are intentionally explicit and centralised.
# ------------------------------------------------------------------

@dataclass(frozen=True)
class Thresholds:
    tau_balance: Optional[float] = None
    tau_bottleneck: Optional[float] = None
    tau_operational: Optional[float] = None

    # New pattern thresholds
    tau_noisy: Optional[float] = None
    tau_uniform_low_mean: Optional[float] = None
    tau_uniform_high_mean: Optional[float] = None
    tau_polarised_range: Optional[float] = None
    tau_low: Optional[float] = None
    tau_high: Optional[float] = None

THRESHOLDS = Thresholds(
    tau_balance=0.12,            # std ≤ 0.12 → scores are fairly even
    tau_bottleneck=0.25,         # min score ≤ 0.25 → clear low-end weakness
    tau_operational=0.30,        # generic hard gate (dimension / group)    # Can be discarded

    # NOTE : NEW (COUPLED) THRESHOLDS ADDED IN VERSION 1.1.2 (2021-10-10)
    tau_noisy=0.22,              # std ≥ 0.22 → unstable / inconsistent profile
    tau_uniform_low_mean=0.30,   # mean ≤ 0.30 (and balanced) → uniformly weak
    tau_uniform_high_mean=0.70,  # mean ≥ 0.70 (and balanced) → uniformly strong
    tau_polarised_range=0.55,    # range ≥ 0.55 → large internal spread
    tau_low=0.30,                # min ≤ 0.30 → weak extreme
    tau_high=0.70,               # max ≥ 0.70 → strong extreme
)

# ------------------------------------------------------------------
# Percentile conventions (optional, descriptive only)
# ------------------------------------------------------------------

PERCENTILES_ENABLED_DEFAULT = True
PERCENTILE_SCALE = "0_to_1"      # (rank - 1) / (N - 1)
RANK_TIE_METHOD = "average"
RANK_HIGHER_IS_BETTER = True


# ------------------------------------------------------------------
# Explicit exclusions / scope limits
# These protect PPD from drifting into predictive or evaluative use.
# ------------------------------------------------------------------

ALLOW_ZSCORES = False
ALLOW_COMPOSITE_QUALITY_SCORE = False
ALLOW_SUITABILITY_INFERENCE = False
ALLOW_PREDICTION = False
ALLOW_RANKING_DEFAULT = False


# ------------------------------------------------------------------
# Validation behaviour
# ------------------------------------------------------------------

STRICT_SCHEMA_VALIDATION = True
CLAMP_OUT_OF_RANGE_INPUTS = False
