"""Confidence-Weighted Global Constraint Projection (CW-GCP).

The package is intentionally independent from the InstructScene runtime.  It
operates on exported 2D floor-plane layouts and can therefore be tested and
audited without loading a generator checkpoint.
"""

from src.cwgcp.repairer import repair_layout_cwgcp
from src.cwgcp.types import (
    CWGCPConfig,
    LayoutObject,
    RelationProposal,
    RepairResult,
    ResolvedRelation,
)

__all__ = [
    "CWGCPConfig",
    "LayoutObject",
    "RelationProposal",
    "RepairResult",
    "ResolvedRelation",
    "repair_layout_cwgcp",
]
