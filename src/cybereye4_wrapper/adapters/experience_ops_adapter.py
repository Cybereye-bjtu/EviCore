"""经验抽取与经验库 → Neo4j 同步：封装 `experience.extractor` / `experience.neo4j_sync`。"""

from __future__ import annotations

from typing import Any, Dict

from cybereye4_wrapper.adapters.project_loader import ensure_cybereye_on_path


def extract_and_post_process(
    src_root: str,
    question: str,
    answer: str,
    *,
    post_process: bool = True,
) -> Dict[str, Any]:
    ensure_cybereye_on_path(src_root)
    from experience.extractor import extract_experience, post_process_experience

    raw = extract_experience(question, answer)
    if post_process:
        return post_process_experience(raw)
    return raw if isinstance(raw, dict) else {"raw": raw}


def sync_experience_store(
    src_root: str,
    store_path: str,
) -> Dict[str, Any]:
    """
    将 `experience_store.json`（数组）同步到 Neo4j 经验层。
    返回 {written_count, store_path}；驱动不可用时 written_count 为 -1。
    """
    ensure_cybereye_on_path(src_root)
    from experience.neo4j_sync import sync_experience_store_to_neo4j

    n = sync_experience_store_to_neo4j(store_path)
    return {"written_count": n, "store_path": store_path}
