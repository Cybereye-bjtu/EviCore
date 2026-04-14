"""CLI: solve | kg-pipeline | extract-experience | sync-experience | evaluate | capabilities"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict


def _dump(obj: Any, output_path: str) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


def _cmd_solve(args: argparse.Namespace) -> int:
    from cybereye4_wrapper.engine import solve_with_knowledge

    with open(args.input, encoding="utf-8") as f:
        payload: Dict[str, Any] = json.load(f)
    q = str(payload.get("question") or "").strip()
    if not q:
        print("error: 'question' is required in JSON", file=sys.stderr)
        return 2
    result = solve_with_knowledge(
        question=q,
        scene_path=payload.get("scene_path"),
        current_region=payload.get("current_region"),
        object_information=payload.get("object_information"),
        region_names=payload.get("region_names"),
        use_kg=bool(payload.get("use_kg", True)),
        use_experience=bool(payload.get("use_experience", True)),
    )
    _dump(result, args.output)
    return 0 if not result.get("error") else 1


def _cmd_kg_pipeline(args: argparse.Namespace) -> int:
    from cybereye4_wrapper.capabilities import run_kg_pipeline

    body: Dict[str, Any] = {}
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            body = json.load(f)
    result = run_kg_pipeline(
        sample_kb_dir=body.get("sample_kb_dir"),
        output_json=body.get("output_json"),
        sync_neo4j=body.get("sync_neo4j"),
        strict_samples=bool(body.get("strict_samples", True)),
        force_reextract_all=bool(body.get("force_reextract_all", False)),
    )
    _dump(result, args.output)
    return 0 if not result.get("error") else 1


def _cmd_extract_experience(args: argparse.Namespace) -> int:
    from cybereye4_wrapper.capabilities import extract_experience_record

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            body = json.load(f)
    else:
        if not (args.question and args.answer):
            print("error: provide --input JSON or both --question and --answer", file=sys.stderr)
            return 2
        body = {"question": args.question, "answer": args.answer, "post_process": not args.no_post_process}
    result = extract_experience_record(
        question=str(body.get("question") or "").strip(),
        answer=str(body.get("answer") or "").strip(),
        post_process=bool(body.get("post_process", True)),
    )
    _dump(result, args.output)
    return 0 if not result.get("error") else 1


def _cmd_sync_experience(args: argparse.Namespace) -> int:
    from cybereye4_wrapper.capabilities import sync_experience_store_to_graph

    result = sync_experience_store_to_graph(store_path=args.store_path)
    _dump(result, args.output)
    return 0 if not result.get("error") else 1


def _cmd_evaluate(args: argparse.Namespace) -> int:
    from cybereye4_wrapper.capabilities import evaluate_answer_dimension, score_answers_from_file

    if args.mode == "file":
        with open(args.input, encoding="utf-8") as f:
            body = json.load(f)
        result = score_answers_from_file(
            answer_file=str(body.get("answer_file") or ""),
            ground_truth_path=body.get("ground_truth_path"),
            evaluator=str(body.get("evaluator", "dmxapi")),
            model=str(body.get("model", "gemini-2.0-flash")),
            api_key=str(body.get("api_key", "")),
            base_url=str(body.get("base_url", "https://www.dmxapi.cn/v1")),
            timeout=int(body.get("timeout", 120)),
            force=bool(body.get("force", False)),
            overwrite_output=bool(body.get("overwrite_output", False)),
            score_direct=bool(body.get("score_direct", True)),
            score_reasoning=bool(body.get("score_reasoning", True)),
            implicit_eqa_id=str(body.get("implicit_eqa_id", "")),
            scene_path_substr=str(body.get("scene_path_substr", "")),
            exclude_id_range=str(body.get("exclude_id_range", "")),
            sleep_sec=float(body.get("sleep_sec", 0.0)),
        )
    else:
        with open(args.input, encoding="utf-8") as f:
            body = json.load(f)
        result = evaluate_answer_dimension(
            prompt_name=str(body.get("prompt_name") or "direct"),
            prompt_kwargs=dict(body.get("prompt_kwargs") or {}),
            evaluator=str(body.get("evaluator", "dmxapi")),
            model=str(body.get("model", "gemini-2.0-flash")),
            api_key=str(body.get("api_key", "")),
            base_url=str(body.get("base_url", "https://www.dmxapi.cn/v1")),
            timeout=int(body.get("timeout", 120)),
        )
    _dump(result, args.output)
    return 0 if not result.get("error") else 1


def _cmd_capabilities(args: argparse.Namespace) -> int:
    from cybereye4_wrapper.capabilities import list_capabilities

    _dump(list_capabilities(), args.output)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cybereye4_wrapper",
        description="Cybereye4 wrapper CLI — set CYBEREYE_SRC_ROOT to the Cybereye4 project root.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_solve = sub.add_parser("solve", help="Knowledge-augmented solve (Planner1/2 + KG + experience)")
    p_solve.add_argument("-i", "--input", required=True, help="JSON with question, object_information, ...")
    p_solve.add_argument("-o", "--output", default="", help="Write JSON result to file")
    p_solve.set_defaults(func=_cmd_solve)

    p_kg = sub.add_parser("kg-pipeline", help="Run sample_kb → layers JSON → Neo4j incremental pipeline")
    p_kg.add_argument(
        "-i",
        "--input",
        default="",
        help="Optional JSON: sample_kb_dir, output_json, sync_neo4j, strict_samples, force_reextract_all",
    )
    p_kg.add_argument("-o", "--output", default="", help="Write result JSON to file")
    p_kg.set_defaults(func=_cmd_kg_pipeline)

    p_ex = sub.add_parser("extract-experience", help="extract_experience + post_process from Q/A")
    p_ex.add_argument("-i", "--input", default="", help="JSON with question, answer [, post_process]")
    p_ex.add_argument("--question", default="", help="If no -i: question text")
    p_ex.add_argument("--answer", default="", help="If no -i: answer text")
    p_ex.add_argument("--no-post-process", action="store_true", help="Skip post_process_experience")
    p_ex.add_argument("-o", "--output", default="", help="Write result JSON to file")
    p_ex.set_defaults(func=_cmd_extract_experience)

    p_sync = sub.add_parser("sync-experience", help="Sync experience_store.json to Neo4j experience layer")
    p_sync.add_argument("store_path", help="Path to experience_store.json")
    p_sync.add_argument("-o", "--output", default="", help="Write result JSON to file")
    p_sync.set_defaults(func=_cmd_sync_experience)

    p_ev = sub.add_parser("evaluate", help="LLM scoring: score-file | one-shot prompt")
    p_ev.add_argument(
        "mode",
        choices=("file", "one"),
        help="file: score CyberEyeEQAanswer.json; one: single evaluate_answer call",
    )
    p_ev.add_argument(
        "-i",
        "--input",
        required=True,
        help="JSON body matching POST /evaluate/score-file or /evaluate/one",
    )
    p_ev.add_argument("-o", "--output", default="", help="Write result JSON to file")
    p_ev.set_defaults(func=_cmd_evaluate)

    p_cap = sub.add_parser("capabilities", help="Print capability map (modules in Cybereye4)")
    p_cap.add_argument("-o", "--output", default="", help="Write JSON to file")
    p_cap.set_defaults(func=_cmd_capabilities)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
