"""Experience layer: build_experience_context + merge into Planner1 knowledge text."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from cybereye4_wrapper.adapters.project_loader import ensure_cybereye_on_path


def merge_experience_into_knowledge(
    src_root: str,
    base_knowledge: str,
    question: str,
    scene_path: str,
    use_experience: bool,
) -> Tuple[str, Dict[str, Any]]:
    """
    Reuses Cybereye4 `build_experience_context` and `merge_knowledge_and_experience_text`,
    plus optional scene memory / observation memory blocks (same as main.py ordering, without writing files).
    """
    ensure_cybereye_on_path(src_root)
    if not use_experience:
        return base_knowledge or "", {}

    from experience.object_memory import normalize_scene_key
    from knowledge_graph.experience_context import (
        build_experience_context,
        collect_relevant_scene_memory_facts,
        merge_knowledge_and_experience_text,
        render_scene_memory_facts_text,
    )

    scene_path = (scene_path or "").strip()
    sk_norm = normalize_scene_key(scene_path) if scene_path else ""

    ctx: Dict[str, Any] = build_experience_context(question, scene_path=scene_path)
    exp_text_raw = str(ctx.get("experience_context_text") or "")
    merged, combined = merge_knowledge_and_experience_text(base_knowledge or "", exp_text_raw)

    facts: List[Dict[str, Any]] = collect_relevant_scene_memory_facts(
        question_text=question,
        matched_experiences=ctx.get("matched_experiences") or [],
        scene_key=sk_norm,
        topk=20,
    )
    facts_text = render_scene_memory_facts_text(facts)
    obs_txt = str(ctx.get("observation_memory_text") or "").strip()
    extra_blocks: List[str] = []
    if facts_text.strip():
        extra_blocks.append(facts_text.strip())
    if obs_txt:
        extra_blocks.append(obs_txt)
    combo_extra = "\n\n".join(extra_blocks)
    if combo_extra:
        marker = "\n\n[Past useful experience]\n"
        if marker in merged:
            left, right = merged.split(marker, 1)
            left = left.rstrip()
            merged = (
                (left + "\n\n" if left else "")
                + combo_extra
                + marker
                + right.lstrip()
            ).rstrip()
        else:
            merged = (
                (combo_extra + "\n\n" + merged.lstrip()).rstrip()
                if merged.strip()
                else combo_extra
            )

    ctx["scene_memory_facts_selected"] = facts
    ctx["combined_into_knowledge_text"] = combined
    return merged, ctx
