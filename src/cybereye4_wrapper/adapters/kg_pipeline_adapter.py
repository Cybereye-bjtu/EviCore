"""样本库 → 三层 JSON → Neo4j：封装 Cybereye4 `knowledge_graph.pipeline`。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from cybereye4_wrapper.adapters.project_loader import ensure_cybereye_on_path


def run_incremental_pipeline(
    src_root: str,
    *,
    sample_kb_dir: Optional[str] = None,
    output_json: Optional[str] = None,
    sync_neo4j: Optional[bool] = None,
    strict_samples: bool = True,
    force_reextract_all: bool = False,
    log_prefix: str = "[KG:wrapper]",
) -> Dict[str, Any]:
    ensure_cybereye_on_path(src_root)
    from knowledge_graph.pipeline import run_incremental_pipeline as _run

    return _run(
        sample_kb_dir=sample_kb_dir,
        output_json=output_json,
        sync_neo4j=sync_neo4j,
        strict_samples=strict_samples,
        force_reextract_all=force_reextract_all,
        log_prefix=log_prefix,
    )
