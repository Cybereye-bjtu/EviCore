"""
可调用能力扩展：知识建图管线、经验抽取 / 同步、EQA 答案评估。

均通过 CYBEREYE_SRC_ROOT 加载 Cybereye4 模块，不修改原仓库。
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from cybereye4_wrapper.adapters import evaluation_adapter, experience_ops_adapter, kg_pipeline_adapter
from cybereye4_wrapper.config import get_settings


def _err(t: str, msg: str) -> Dict[str, Any]:
    return {"type": t, "message": msg}


def run_kg_pipeline(
    sample_kb_dir: Optional[str] = None,
    output_json: Optional[str] = None,
    sync_neo4j: Optional[bool] = None,
    strict_samples: bool = True,
    force_reextract_all: bool = False,
) -> Dict[str, Any]:
    """
    样本库 → 增量三层 JSON →（可选）Neo4j 同步。

    映射：`knowledge_graph.pipeline.run_incremental_pipeline`
    """
    trace: List[Dict[str, Any]] = []
    out: Dict[str, Any] = {
        "summary": None,
        "trace": trace,
        "error": None,
    }
    try:
        settings = get_settings()
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        trace.append({"step": "settings", "ok": False})
        return out

    try:
        summary = kg_pipeline_adapter.run_incremental_pipeline(
            settings.cybereye_src_root,
            sample_kb_dir=sample_kb_dir,
            output_json=output_json,
            sync_neo4j=sync_neo4j,
            strict_samples=strict_samples,
            force_reextract_all=force_reextract_all,
        )
        out["summary"] = summary
        trace.append({"step": "knowledge_graph.pipeline", "ok": True})
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        trace.append(
            {
                "step": "knowledge_graph.pipeline",
                "ok": False,
                "detail": traceback.format_exc()[-8000:],
            }
        )
    return out


def extract_experience_record(
    question: str,
    answer: str,
    post_process: bool = True,
) -> Dict[str, Any]:
    """
    从 (question, answer) 抽取结构化经验字段。

    映射：`experience.extractor.extract_experience` → `post_process_experience`
    """
    trace: List[Dict[str, Any]] = []
    out: Dict[str, Any] = {
        "experience": None,
        "trace": trace,
        "error": None,
    }
    try:
        settings = get_settings()
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        return out

    try:
        exp = experience_ops_adapter.extract_and_post_process(
            settings.cybereye_src_root,
            question,
            answer,
            post_process=post_process,
        )
        out["experience"] = exp
        trace.append({"step": "experience.extract", "ok": True})
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        trace.append(
            {"step": "experience.extract", "ok": False, "detail": traceback.format_exc()[-8000:]}
        )
    return out


def sync_experience_store_to_graph(store_path: str) -> Dict[str, Any]:
    """
    将 experience_store.json 写入 Neo4j 经验层。

    映射：`experience.neo4j_sync.sync_experience_store_to_neo4j`
    """
    trace: List[Dict[str, Any]] = []
    out: Dict[str, Any] = {
        "written_count": None,
        "store_path": store_path,
        "trace": trace,
        "error": None,
    }
    try:
        settings = get_settings()
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        return out

    try:
        res = experience_ops_adapter.sync_experience_store(settings.cybereye_src_root, store_path)
        out["written_count"] = res.get("written_count")
        trace.append({"step": "experience.neo4j_sync", "ok": True})
        if out["written_count"] == -1:
            out["error"] = _err(
                "DriverUnavailable",
                "Neo4j driver unavailable; check NEO4J_PASSWORD and neo4j package.",
            )
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        trace.append(
            {"step": "experience.neo4j_sync", "ok": False, "detail": traceback.format_exc()[-8000:]}
        )
    return out


def score_answers_from_file(
    answer_file: str,
    ground_truth_path: Optional[str] = None,
    evaluator: str = "dmxapi",
    model: str = "gemini-2.0-flash",
    api_key: str = "",
    base_url: str = "https://www.dmxapi.cn/v1",
    timeout: int = 120,
    force: bool = False,
    overwrite_output: bool = False,
    score_direct: bool = True,
    score_reasoning: bool = True,
    implicit_eqa_id: str = "",
    scene_path_substr: str = "",
    exclude_id_range: str = "",
    sleep_sec: float = 0.0,
) -> Dict[str, Any]:
    """
    对 CyberEyeEQAanswer.json 做 LLM 评分（direct / reasoning，0–5）。

    映射：`evaluation.score_cybereye_answers.score_answer_file`
    """
    trace: List[Dict[str, Any]] = []
    out: Dict[str, Any] = {
        "result": None,
        "trace": trace,
        "error": None,
    }
    try:
        settings = get_settings()
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        return out

    import os

    key = api_key or os.environ.get("ANSWER_EVAL_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    if not key:
        out["error"] = _err(
            "ValueError",
            "Missing API key: pass api_key or set ANSWER_EVAL_API_KEY / OPENAI_API_KEY.",
        )
        return out

    try:
        raw = evaluation_adapter.score_answer_file(
            settings.cybereye_src_root,
            answer_file=answer_file,
            ground_truth_path=ground_truth_path,
            evaluator=evaluator,
            model=model,
            api_key=key,
            base_url=base_url,
            timeout=timeout,
            force=force,
            overwrite_output=overwrite_output,
            score_direct=score_direct,
            score_reasoning=score_reasoning,
            implicit_eqa_id=implicit_eqa_id,
            scene_path_substr=scene_path_substr,
            exclude_id_range=exclude_id_range,
            sleep_sec=sleep_sec,
        )
        out["result"] = raw
        trace.append({"step": "evaluation.score_answer_file", "ok": True})
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        trace.append(
            {
                "step": "evaluation.score_answer_file",
                "ok": False,
                "detail": traceback.format_exc()[-8000:],
            }
        )
    return out


def evaluate_answer_dimension(
    prompt_name: str,
    prompt_kwargs: Dict[str, str],
    evaluator: str = "dmxapi",
    model: str = "gemini-2.0-flash",
    api_key: str = "",
    base_url: str = "https://www.dmxapi.cn/v1",
    timeout: int = 120,
) -> Dict[str, Any]:
    """
    单次调用评分（加载 `prompts/{prompt_name}.txt`），返回 score / raw / brief_reason。

    映射：`evaluation.score_cybereye_answers.evaluate_answer`
    """
    trace: List[Dict[str, Any]] = []
    out: Dict[str, Any] = {
        "scores": None,
        "trace": trace,
        "error": None,
    }
    try:
        settings = get_settings()
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        return out

    import os

    key = api_key or os.environ.get("ANSWER_EVAL_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    if not key:
        out["error"] = _err(
            "ValueError",
            "Missing API key: pass api_key or set ANSWER_EVAL_API_KEY / OPENAI_API_KEY.",
        )
        return out

    try:
        raw = evaluation_adapter.evaluate_one(
            settings.cybereye_src_root,
            evaluator=evaluator,
            model=model,
            api_key=key,
            base_url=base_url,
            timeout=timeout,
            prompt_name=prompt_name,
            prompt_kwargs=prompt_kwargs,
        )
        out["scores"] = raw
        trace.append({"step": "evaluation.evaluate_answer", "ok": True})
    except Exception as e:
        out["error"] = _err(type(e).__name__, str(e))
        trace.append(
            {
                "step": "evaluation.evaluate_answer",
                "ok": False,
                "detail": traceback.format_exc()[-8000:],
            }
        )
    return out


def list_capabilities() -> Dict[str, Any]:
    """OpenAPI / CLI 用的能力清单（说明映射到 Cybereye4 的哪些模块）。"""
    import cybereye4_wrapper as _pkg

    return {
        "version": getattr(_pkg, "__version__", "0.2.0"),
        "layers": {
            "decision": {
                "entry": "solve_with_knowledge",
                "maps_to": [
                    "Agent.llmAgent.Planner1 / Planner2",
                    "knowledge_graph.planner1_graph",
                    "knowledge_graph.experience_context",
                ],
            },
            "knowledge_graph_pipeline": {
                "entry": "run_kg_pipeline",
                "maps_to": ["knowledge_graph.pipeline.run_incremental_pipeline"],
                "description": "样本库增量抽取三层 JSON，可选同步 Neo4j。",
            },
            "experience": {
                "extract": {
                    "entry": "extract_experience_record",
                    "maps_to": [
                        "experience.extractor.extract_experience",
                        "experience.extractor.post_process_experience",
                    ],
                },
                "sync_neo4j": {
                    "entry": "sync_experience_store_to_graph",
                    "maps_to": ["experience.neo4j_sync.sync_experience_store_to_neo4j"],
                },
            },
            "evaluation": {
                "score_file": {
                    "entry": "score_answers_from_file",
                    "maps_to": ["evaluation.score_cybereye_answers.score_answer_file"],
                },
                "evaluate_one": {
                    "entry": "evaluate_answer_dimension",
                    "maps_to": ["evaluation.score_cybereye_answers.evaluate_answer"],
                },
            },
        },
    }
