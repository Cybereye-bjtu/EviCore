"""FastAPI：问答决策 + 知识建图 + 经验 + 评估。"""

from __future__ import annotations

from cybereye4_wrapper import __version__
from cybereye4_wrapper.capabilities import (
    evaluate_answer_dimension,
    extract_experience_record,
    list_capabilities,
    run_kg_pipeline,
    score_answers_from_file,
    sync_experience_store_to_graph,
)
from cybereye4_wrapper.engine import solve_with_knowledge
from cybereye4_wrapper.schemas.capabilities import (
    EvaluateOneRequest,
    EvaluateScoreFileRequest,
    ExtractExperienceRequest,
    KgPipelineRequest,
    SyncExperienceStoreRequest,
)
from cybereye4_wrapper.schemas.request import SolveRequest
from fastapi import FastAPI

app = FastAPI(
    title="Cybereye4 Knowledge & Ops API (wrapper)",
    version=__version__,
    description=(
        "统一调用层：知识增强问答与决策（Planner1/2）、样本库建图管线、经验抽取/同步、EQA LLM 评估。"
        "依赖环境变量 CYBEREYE_SRC_ROOT 指向 Cybereye4 工程根目录。"
    ),
    openapi_tags=[
        {"name": "core", "description": "决策引擎 `solve_with_knowledge`"},
        {"name": "knowledge_graph", "description": "样本库 → 三层 JSON → Neo4j"},
        {"name": "experience", "description": "经验抽取与 experience_store → Neo4j"},
        {"name": "evaluation", "description": "CyberEyeEQAanswer LLM 评分"},
        {"name": "meta", "description": "健康检查与能力清单"},
    ],
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "wrapper_version": __version__}


@app.get("/capabilities", tags=["meta"])
def get_capabilities() -> dict:
    """返回可调用的能力入口及对应的 Cybereye4 源码映射。"""
    return list_capabilities()


@app.post("/solve", tags=["core"])
def post_solve(body: SolveRequest) -> dict:
    return solve_with_knowledge(
        question=body.question,
        scene_path=body.scene_path,
        current_region=body.current_region,
        object_information=body.object_information,
        region_names=body.region_names,
        use_kg=body.use_kg,
        use_experience=body.use_experience,
    )


@app.post("/kg/pipeline", tags=["knowledge_graph"])
def post_kg_pipeline(body: KgPipelineRequest) -> dict:
    return run_kg_pipeline(
        sample_kb_dir=body.sample_kb_dir,
        output_json=body.output_json,
        sync_neo4j=body.sync_neo4j,
        strict_samples=body.strict_samples,
        force_reextract_all=body.force_reextract_all,
    )


@app.post("/experience/extract", tags=["experience"])
def post_experience_extract(body: ExtractExperienceRequest) -> dict:
    return extract_experience_record(
        question=body.question,
        answer=body.answer,
        post_process=body.post_process,
    )


@app.post("/experience/sync-store", tags=["experience"])
def post_experience_sync(body: SyncExperienceStoreRequest) -> dict:
    return sync_experience_store_to_graph(store_path=body.store_path)


@app.post("/evaluate/score-file", tags=["evaluation"])
def post_evaluate_score_file(body: EvaluateScoreFileRequest) -> dict:
    return score_answers_from_file(
        answer_file=body.answer_file,
        ground_truth_path=body.ground_truth_path,
        evaluator=body.evaluator,
        model=body.model,
        api_key=body.api_key,
        base_url=body.base_url,
        timeout=body.timeout,
        force=body.force,
        overwrite_output=body.overwrite_output,
        score_direct=body.score_direct,
        score_reasoning=body.score_reasoning,
        implicit_eqa_id=body.implicit_eqa_id,
        scene_path_substr=body.scene_path_substr,
        exclude_id_range=body.exclude_id_range,
        sleep_sec=body.sleep_sec,
    )


@app.post("/evaluate/one", tags=["evaluation"])
def post_evaluate_one(body: EvaluateOneRequest) -> dict:
    return evaluate_answer_dimension(
        prompt_name=body.prompt_name,
        prompt_kwargs=body.prompt_kwargs,
        evaluator=body.evaluator,
        model=body.model,
        api_key=body.api_key,
        base_url=body.base_url,
        timeout=body.timeout,
    )
