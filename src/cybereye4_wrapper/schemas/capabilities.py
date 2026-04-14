"""请求体：知识建图管线、经验抽取、答案评估。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class KgPipelineRequest(BaseModel):
    """对应 `knowledge_graph.pipeline.run_incremental_pipeline`。"""

    sample_kb_dir: Optional[str] = Field(
        None,
        description="样本库目录；默认使用 Cybereye4 cybereye_config.SAMPLE_KB_DIR。",
    )
    output_json: Optional[str] = Field(
        None,
        description="输出的 knowledge_layers.json 路径；默认 GENERATED_KB_DIR/knowledge_layers.json。",
    )
    sync_neo4j: Optional[bool] = Field(
        None,
        description="是否同步 Neo4j；None 表示跟随管线默认（通常为 True）。",
    )
    strict_samples: bool = Field(True, description="样本加载是否严格模式。")
    force_reextract_all: bool = Field(False, description="True 时忽略 manifest 缓存，全量重抽。")


class ExtractExperienceRequest(BaseModel):
    """对应 `experience.extractor.extract_experience` + `post_process_experience`。"""

    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1, description="模型或人工给出的答案文本，用于抽取结构化经验。")
    post_process: bool = Field(True, description="是否做 post_process_experience 规范化。")


class SyncExperienceStoreRequest(BaseModel):
    """对应 `experience.neo4j_sync.sync_experience_store_to_neo4j`。"""

    store_path: str = Field(
        ...,
        min_length=1,
        description="experience_store.json 绝对路径或当前工作目录下可读路径。",
    )


class EvaluateScoreFileRequest(BaseModel):
    """对应 `evaluation.score_cybereye_answers.score_answer_file`。"""

    answer_file: str = Field(..., min_length=1, description="CyberEyeEQAanswer.json 路径。")
    ground_truth_path: Optional[str] = Field(
        None,
        description="默认 {CYBEREYE_SRC_ROOT}/Data/EQA.json。",
    )
    evaluator: str = Field("dmxapi", description="dmxapi | qwen | openai")
    model: str = Field("gemini-2.0-flash")
    api_key: str = Field("", description="缺省读环境变量 ANSWER_EVAL_API_KEY / OPENAI_API_KEY。")
    base_url: str = Field("https://www.dmxapi.cn/v1")
    timeout: int = Field(120, ge=5, le=600)
    force: bool = False
    overwrite_output: bool = False
    score_direct: bool = True
    score_reasoning: bool = True
    implicit_eqa_id: str = ""
    scene_path_substr: str = ""
    exclude_id_range: str = ""
    sleep_sec: float = 0.0


class EvaluateOneRequest(BaseModel):
    """单条 prompt 评分（无 answer 文件时演示用）。"""

    evaluator: str = Field("dmxapi")
    model: str = Field("gemini-2.0-flash")
    api_key: str = Field("")
    base_url: str = Field("https://www.dmxapi.cn/v1")
    timeout: int = Field(120, ge=5, le=600)
    prompt_name: str = Field(
        ...,
        description="prompts 下模板名：通常为 direct 或 reasoning（与 score_cybereye_answers 一致）。",
    )
    prompt_kwargs: Dict[str, str] = Field(
        ...,
        description="与模板占位符一致的键值，如 question, ground_truth_direct_answer, model_direct_answer。",
    )
