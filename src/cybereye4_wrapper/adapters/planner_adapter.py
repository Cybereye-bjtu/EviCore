"""Planner1 / Planner2 via Cybereye4 Agent.llmAgent (real LLM calls)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from cybereye4_wrapper.adapters.project_loader import ensure_cybereye_on_path


def _make_client(api_key: Optional[str], base_url: Optional[str]) -> OpenAI:
    kwargs: Dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def run_planner1(
    src_root: str,
    *,
    question: str,
    object_list: List[str],
    information_list: Dict[str, List[Any]],
    knowledge_text: str,
    graph_context: str,
    region_names: Optional[List[str]],
    model: str,
    api_key: Optional[str],
    base_url: Optional[str],
) -> Dict[str, Any]:
    ensure_cybereye_on_path(src_root)
    from Agent.llmAgent import Planner1

    client = _make_client(api_key, base_url)
    planner = Planner1(client, model=model)
    return planner.decide(
        question=question,
        object_list=object_list,
        information_list=information_list,
        knowledge_text=knowledge_text or "",
        region_names=region_names,
        graph_context=graph_context or "",
        iteration=1,
    )


def run_planner2(
    src_root: str,
    *,
    reason: str,
    current_region: Optional[str],
    region_names: Optional[List[str]],
    model: str,
    api_key: Optional[str],
    base_url: Optional[str],
) -> Dict[str, Any]:
    ensure_cybereye_on_path(src_root)
    from Agent.llmAgent import Planner2

    client = _make_client(api_key, base_url)
    planner = Planner2(client, model=model)
    return planner.extract_targets(
        reason=reason,
        current_region=current_region,
        region_names=region_names,
    )
