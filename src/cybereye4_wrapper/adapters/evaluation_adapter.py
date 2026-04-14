"""EQA 答案 LLM 评分：封装 `evaluation.score_cybereye_answers`。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from cybereye4_wrapper.adapters.project_loader import ensure_cybereye_on_path


def score_answer_file(
    src_root: str,
    *,
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
    ensure_cybereye_on_path(src_root)
    from evaluation.score_cybereye_answers import score_answer_file as _score

    gt = ground_truth_path
    if not gt:
        import os

        gt = os.path.join(src_root, "Data", "EQA.json")

    return _score(
        answer_file=answer_file,
        ground_truth_path=gt,
        evaluator=evaluator,
        model=model,
        api_key=api_key,
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


def evaluate_one(
    src_root: str,
    *,
    evaluator: str,
    model: str,
    api_key: str,
    base_url: str,
    timeout: int,
    prompt_name: str,
    prompt_kwargs: Dict[str, str],
) -> Dict[str, Any]:
    """单条 LLM 评分（direct 或 reasoning prompt），便于无文件演示。"""
    ensure_cybereye_on_path(src_root)
    from evaluation.score_cybereye_answers import evaluate_answer

    return evaluate_answer(
        evaluator=evaluator,
        model=model,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        prompt_name=prompt_name,
        prompt_kwargs=prompt_kwargs,
    )
