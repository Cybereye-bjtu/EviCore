"""Unified response shape for `solve_with_knowledge`."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SolveError(BaseModel):
    """Structured error payload when the engine cannot complete normally."""

    type: str = Field(..., description="Short error category, e.g. ImportError, ValueError.")
    message: str = Field(..., description="Human-readable message.")


class SolveResponse(BaseModel):
    """Stable JSON fields returned to API and CLI consumers."""

    can_answer: Optional[bool] = None
    direct_answer: str = ""
    reasoning_answer: str = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)
    retrieved_knowledge: Dict[str, Any] = Field(default_factory=dict)
    suggested_targets: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[SolveError] = None

    model_config = {"extra": "allow"}
