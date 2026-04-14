"""
Unified entry: knowledge-enhanced Q&A / decision (Planner1 + optional KG + experience).

Delegates to Cybereye4 modules after CYBEREYE_SRC_ROOT is on sys.path.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from cybereye4_wrapper.adapters import experience_adapter, kg_adapter, planner_adapter
from cybereye4_wrapper.adapters.project_loader import ensure_cybereye_on_path
from cybereye4_wrapper.config import get_settings


def _normalize_object_information(
    raw: Optional[Dict[str, Any]],
    current_region: Optional[str],
) -> Dict[str, List[Any]]:
    """Accept ObjectManager-shaped dict or simplified {obj: 'info string'}."""
    if not raw:
        return {}
    out: Dict[str, List[Any]] = {}
    reg_default = (current_region or "").strip()
    for key, val in raw.items():
        obj_name = str(key).strip() or "object"
        if isinstance(val, list):
            rows: List[Any] = []
            for item in val:
                if isinstance(item, dict):
                    row = dict(item)
                    if "object" not in row:
                        row["object"] = obj_name
                    if reg_default and not str(row.get("region") or "").strip():
                        row["region"] = reg_default
                    rows.append(row)
                else:
                    rows.append(
                        {
                            "object": obj_name,
                            "region": reg_default,
                            "information": str(item),
                        }
                    )
            out[obj_name] = rows
        elif isinstance(val, dict):
            row = dict(val)
            if "object" not in row:
                row["object"] = obj_name
            if reg_default and not str(row.get("region") or "").strip():
                row["region"] = reg_default
            out[obj_name] = [row]
        else:
            out[obj_name] = [
                {
                    "object": obj_name,
                    "region": reg_default,
                    "information": str(val),
                }
            ]
    return out


def _object_list_from_information(information_list: Dict[str, List[Any]]) -> List[str]:
    return [str(k).strip() for k in information_list.keys() if str(k).strip()]


def _base_knowledge_from_observations(
    information_list: Dict[str, List[Any]],
    current_region: Optional[str],
) -> str:
    """Human-readable block when no EQA-scoped get_knowledge_text is used."""
    lines: List[str] = []
    if current_region:
        lines.append(f"[Context] Current region (hint): {current_region}")
    if not information_list:
        lines.append(
            "[Context] No structured object observations were provided. "
            "Planner1 may require on-site information before answering."
        )
        return "\n".join(lines)
    lines.append("[Currently acquired information (structured)]")
    for obj, infos in information_list.items():
        for item in infos or []:
            if isinstance(item, dict):
                o = item.get("object", obj)
                r = item.get("region", "")
                inf = item.get("information", "")
                lines.append(f"- object={o}, region={r}, information={inf}")
            else:
                lines.append(f"- {obj}: {item}")
    return "\n".join(lines)


def _compact_experience_for_response(exp_ctx: Dict[str, Any]) -> Dict[str, Any]:
    matched = exp_ctx.get("matched_experiences") or []
    snippets: List[Dict[str, Any]] = []
    for row in matched[:5]:
        if not isinstance(row, dict):
            continue
        snippets.append(
            {
                "experience_id": row.get("experience_id") or row.get("id"),
                "evidence_summary_text": (row.get("evidence_summary_text") or "")[:500],
                "final_score": row.get("final_score"),
            }
        )
    return {
        "question_type": exp_ctx.get("question_type"),
        "target_scope": exp_ctx.get("target_scope"),
        "semantic_classification": exp_ctx.get("semantic_classification"),
        "ranking_meta": exp_ctx.get("ranking_meta"),
        "matched_count": len(matched),
        "snippets": snippets,
        "experience_context_note": exp_ctx.get("experience_context_note"),
    }


def solve_with_knowledge(
    question: str,
    scene_path: Optional[str] = None,
    current_region: Optional[str] = None,
    object_information: Optional[dict] = None,
    region_names: Optional[List[str]] = None,
    use_kg: bool = True,
    use_experience: bool = True,
) -> dict:
    """
    Single high-level entry: KG hints + experience retrieval + Planner1 (+ Planner2 if needed).

    Returns a stable JSON dict (see README field list).
    """
    trace: List[Dict[str, Any]] = []
    out: Dict[str, Any] = {
        "can_answer": None,
        "direct_answer": "",
        "reasoning_answer": "",
        "evidence": {},
        "retrieved_knowledge": {},
        "suggested_targets": [],
        "trace": trace,
        "error": None,
    }

    try:
        settings = get_settings()
    except Exception as e:
        out["error"] = {"type": type(e).__name__, "message": str(e)}
        trace.append({"step": "load_settings", "ok": False, "error": str(e)})
        return out

    try:
        ensure_cybereye_on_path(settings.cybereye_src_root)
        trace.append({"step": "ensure_cybereye_on_path", "ok": True, "root": settings.cybereye_src_root})
    except Exception as e:
        out["error"] = {"type": type(e).__name__, "message": str(e)}
        trace.append({"step": "ensure_cybereye_on_path", "ok": False, "error": str(e)})
        return out

    q = (question or "").strip()
    if not q:
        out["error"] = {"type": "ValueError", "message": "question must be non-empty"}
        return out

    information_list = _normalize_object_information(object_information, current_region)
    object_list = _object_list_from_information(information_list)
    base_knowledge = _base_knowledge_from_observations(information_list, current_region)

    kg_trace_sink: List[Dict[str, Any]] = []
    graph_context = ""
    try:
        graph_context, kg_records = kg_adapter.build_graph_context(
            q,
            region_names=region_names,
            use_kg=use_kg,
            trace_sink=kg_trace_sink,
        )
        out["retrieved_knowledge"]["knowledge_graph"] = {
            "enabled": use_kg,
            "context_preview": (graph_context or "")[:2000],
            "trace": kg_records,
        }
        trace.append({"step": "knowledge_graph", "ok": True, "records": len(kg_records)})
    except Exception as e:
        out["retrieved_knowledge"]["knowledge_graph"] = {
            "enabled": use_kg,
            "error": str(e),
            "trace": kg_trace_sink,
        }
        trace.append(
            {
                "step": "knowledge_graph",
                "ok": False,
                "error": str(e),
                "detail": traceback.format_exc()[-4000:],
            }
        )
        graph_context = ""

    merged_knowledge = base_knowledge
    exp_summary: Dict[str, Any] = {}
    try:
        merged_knowledge, exp_ctx = experience_adapter.merge_experience_into_knowledge(
            settings.cybereye_src_root,
            base_knowledge,
            q,
            scene_path or "",
            use_experience,
        )
        exp_summary = _compact_experience_for_response(exp_ctx) if use_experience else {}
        out["retrieved_knowledge"]["experience"] = exp_summary
        trace.append({"step": "experience", "ok": True})
    except Exception as e:
        out["retrieved_knowledge"]["experience"] = {"error": str(e)}
        trace.append(
            {
                "step": "experience",
                "ok": False,
                "error": str(e),
                "detail": traceback.format_exc()[-4000:],
            }
        )
        merged_knowledge = base_knowledge

    out["evidence"] = {
        "object_observations": information_list,
        "current_region": current_region,
        "scene_path": scene_path,
        "knowledge_text_preview": (merged_knowledge or "")[:4000],
    }

    p1: Dict[str, Any] = {}
    try:
        p1 = planner_adapter.run_planner1(
            settings.cybereye_src_root,
            question=q,
            object_list=object_list,
            information_list=information_list,
            knowledge_text=merged_knowledge,
            graph_context=graph_context,
            region_names=region_names,
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        trace.append({"step": "planner1", "ok": True})
    except Exception as e:
        out["error"] = {"type": type(e).__name__, "message": str(e)}
        trace.append(
            {
                "step": "planner1",
                "ok": False,
                "error": str(e),
                "detail": traceback.format_exc()[-4000:],
            }
        )
        return out

    can_answer = bool(p1.get("can_answer"))
    out["can_answer"] = can_answer
    out["direct_answer"] = str(p1.get("direct_answer") or "").strip()
    out["reasoning_answer"] = str(p1.get("reasoning_answer") or "").strip()

    if not can_answer:
        reason = str(p1.get("reason") or "").strip()
        out["reasoning_answer"] = out["reasoning_answer"] or reason
        try:
            p2 = planner_adapter.run_planner2(
                settings.cybereye_src_root,
                reason=reason or "Need more observations.",
                current_region=current_region,
                region_names=region_names,
                model=settings.llm_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
            targets = p2.get("targets") or []
            if isinstance(targets, list):
                out["suggested_targets"] = targets
            trace.append({"step": "planner2", "ok": True})
        except Exception as e:
            trace.append({"step": "planner2", "ok": False, "error": str(e)})
    else:
        trace.append({"step": "planner2", "skipped": True, "reason": "can_answer=True"})

    return out

