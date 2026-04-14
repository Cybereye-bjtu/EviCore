"""HTTP / JSON request models for the solve API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    """Input for `solve_with_knowledge` and POST /solve."""

    question: str = Field(..., min_length=1, description="User question in natural language.")
    scene_path: Optional[str] = Field(
        None,
        description="Scene USD path or identifier; used for experience scene_key and same-scene memory.",
    )
    current_region: Optional[str] = Field(
        None,
        description="Robot / agent current region label; forwarded to Planner2 when suggesting targets.",
    )
    object_information: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "ObjectManager-shaped observations: object name -> list of {object, region, information}, "
            "or a simplified dict of object -> information string."
        ),
    )
    region_names: Optional[List[str]] = Field(
        None,
        description="Whitelist of valid region names for Planner1 / Planner2.",
    )
    use_kg: bool = Field(True, description="Enable Neo4j knowledge-graph hints for Planner1.")
    use_experience: bool = Field(True, description="Enable experience-layer retrieval and merge into knowledge text.")
