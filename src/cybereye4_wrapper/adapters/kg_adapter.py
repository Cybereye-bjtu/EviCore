"""Knowledge-graph context for Planner1 (wraps planner1_graph, no ad-hoc Cypher here)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def build_graph_context(
    question: str,
    *,
    region_names: Optional[List[str]],
    use_kg: bool,
    trace_sink: Optional[List[Dict[str, Any]]],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns (graph_context_string, trace_records).

    When use_kg is False, returns ("", []).
    """
    if not use_kg:
        return "", []

    from knowledge_graph.planner1_graph import build_graph_context_for_planner1

    sink = trace_sink if trace_sink is not None else []
    text = build_graph_context_for_planner1(
        question,
        region_names=region_names,
        trace_sink=sink,
        call_meta={"source": "cybereye4_wrapper.kg_adapter"},
    )
    return text or "", list(sink)
