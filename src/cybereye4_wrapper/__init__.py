"""Cybereye4 wrapper: knowledge-augmented Q&A, KG pipeline, experience, and evaluation."""

from cybereye4_wrapper.capabilities import (
    evaluate_answer_dimension,
    extract_experience_record,
    list_capabilities,
    run_kg_pipeline,
    score_answers_from_file,
    sync_experience_store_to_graph,
)
from cybereye4_wrapper.engine import solve_with_knowledge

__version__ = "0.2.0"
__all__ = [
    "solve_with_knowledge",
    "run_kg_pipeline",
    "extract_experience_record",
    "sync_experience_store_to_graph",
    "score_answers_from_file",
    "evaluate_answer_dimension",
    "list_capabilities",
    "__version__",
]
