#  EviCore — 知识增强问答与决策引擎

本仓库是 **包装层 / 接口层**：通过 `import` 调用 EvidencePilot 工程中的 **Planner1 / Planner2**、**知识图谱**、**经验抽取与检索**、**样本库建图管线**、**EQA LLM 评估**等，对外提供统一 JSON、HTTP 与 CLI。**不会、也不应**修改 EvidencePilot 源码树。

## 能力分层（均可编程调用）

| 层级 | Python 入口 | Cybereye4 映射（只读依赖） |
|------|----------------|----------------------------|
| 决策与问答 | `solve_with_knowledge` | `Agent.llmAgent.Planner1/2`，`knowledge_graph.planner1_graph`，`knowledge_graph.experience_context` |
| 知识建图管线 | `run_kg_pipeline` | `knowledge_graph.pipeline.run_incremental_pipeline`（样本库 → 三层 JSON → Neo4j） |
| 经验抽取 | `extract_experience_record` | `experience.extractor.extract_experience`，`post_process_experience` |
| 经验入库 | `sync_experience_store_to_graph` | `experience.neo4j_sync.sync_experience_store_to_neo4j` |
| 答案评估 | `score_answers_from_file` | `evaluation.score_cybereye_answers.score_answer_file` |
| 单条评分 | `evaluate_answer_dimension` | `evaluation.score_cybereye_answers.evaluate_answer` |
| 能力清单 | `list_capabilities` | 文档/发现用，返回上述映射 |

完整机器可读清单：`GET /capabilities` 或 `python -m cybereye4_wrapper.cli capabilities`。

### `solve_with_knowledge` 返回字段

| 字段 | 说明 |
|------|------|
| `can_answer` | Planner1 是否认为可作答 |
| `direct_answer` | 直接答案（若可答） |
| `reasoning_answer` | 推理说明 |
| `evidence` | 观测、`knowledge_text` 摘要等 |
| `retrieved_knowledge` | 图谱 trace、经验检索摘要 |
| `suggested_targets` | 不可答时 Planner2 的探索目标 |
| `trace` | 各步骤记录 |
| `error` | `{type, message}` 或 `null` |

### 管线 / 抽取 / 评估 返回约定

上述能力统一返回 **`summary` / `experience` / `result` / `scores` + `trace` + `error`** 之一（见各函数 docstring），失败时 `error` 非空并带 `trace` 尾部栈摘要。

## 目录结构

```
cybereye4_wrapper/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── examples/
│   ├── demo_input.json
│   ├── demo_kg_pipeline.json
│   ├── demo_extract_experience.json
│   ├── demo_evaluate_file.json
│   └── demo_evaluate_one.json
├── src/cybereye4_wrapper/
│   ├── __init__.py
│   ├── config.py
│   ├── engine.py
│   ├── capabilities.py
│   ├── api.py
│   ├── cli.py
│   ├── adapters/
│   │   ├── project_loader.py
│   │   ├── kg_adapter.py
│   │   ├── kg_pipeline_adapter.py
│   │   ├── planner_adapter.py
│   │   ├── experience_adapter.py
│   │   ├── experience_ops_adapter.py
│   │   └── evaluation_adapter.py
│   └── schemas/
│       ├── request.py
│       ├── response.py
│       └── capabilities.py
└── tests/
```

## 1. 配置原项目路径（必须）

```bash
export CYBEREYE_SRC_ROOT=/home/klzhang/cybereye4
```

或复制 `.env.example` 为 `.env`（`python-dotenv` 在导入配置时加载）。

### LLM 与 Neo4j

- **Planner / 抽取 / 评估**：`OPENAI_API_KEY`，可选 `OPENAI_BASE_URL`；Planner 模型 `CYBEREYE_LLM_MODEL`。评估可额外使用 `ANSWER_EVAL_*`（与 Cybereye4 `cybereye_config` 一致）。
- **Neo4j**：`NEO4J_URI`、`NEO4J_PASSWORD`、`KNOWLEDGE_GRAPH_ENABLED` 等，行为与 Cybereye4 相同。

## 2. 安装

```bash
cd /path/to/cybereye4_wrapper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 3. 启动 API

```bash
export CYBEREYE_SRC_ROOT=/home/klzhang/cybereye4
uvicorn cybereye4_wrapper.api:app --host 0.0.0.0 --port 8088
```

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/capabilities` | 能力清单与源码映射 |
| POST | `/solve` | 知识增强决策（Planner1/2 + KG + 经验） |
| POST | `/kg/pipeline` | 样本库增量建图管线 |
| POST | `/experience/extract` | 从 Q/A 抽取结构化经验 |
| POST | `/experience/sync-store` | `experience_store.json` → Neo4j |
| POST | `/evaluate/score-file` | 对 `CyberEyeEQAanswer.json` 批量 LLM 评分 |
| POST | `/evaluate/one` | 单条 `prompts/{direct|reasoning}` 评分 |

OpenAPI：`/docs`。

## 4. 命令行

```bash
export CYBEREYE_SRC_ROOT=/home/klzhang/cybereye4

# 决策
python -m cybereye4_wrapper.cli solve -i examples/demo_input.json

# 知识建图（可选 JSON 覆盖默认路径）
python -m cybereye4_wrapper.cli kg-pipeline -i examples/demo_kg_pipeline.json

# 经验抽取
python -m cybereye4_wrapper.cli extract-experience -i examples/demo_extract_experience.json

# 经验库同步到 Neo4j
python -m cybereye4_wrapper.cli sync-experience /path/to/experience_store.json

# 评估：整文件 或 单条 prompt
python -m cybereye4_wrapper.cli evaluate file -i examples/demo_evaluate_file.json
python -m cybereye4_wrapper.cli evaluate one -i examples/demo_evaluate_one.json

# 能力清单
python -m cybereye4_wrapper.cli capabilities
```

## 5. Python 调用示例

```python
from cybereye4_wrapper import (
    solve_with_knowledge,
    run_kg_pipeline,
    extract_experience_record,
    sync_experience_store_to_graph,
    score_answers_from_file,
    evaluate_answer_dimension,
)

# 决策
print(solve_with_knowledge(question="...", object_information={})["can_answer"])

# 建图管线（默认使用 Cybereye4 内 SAMPLE_KB_DIR / layers 路径）
print(run_kg_pipeline(force_reextract_all=False))

# 经验
print(extract_experience_record("Why is the indicator green?", "Because ..."))

# 评估（需 API key）
print(score_answers_from_file("/path/to/CyberEyeEQAanswer.json"))
print(
    evaluate_answer_dimension(
        prompt_name="direct",
        prompt_kwargs={
            "question": "...",
            "ground_truth_direct_answer": "...",
            "model_direct_answer": "...",
        },
    )
)
```

## 设计说明

- **原项目仅作为能力源**：运行时把 `CYBEREYE_SRC_ROOT` 置于 `sys.path` 首位再导入。
- **不对外暴露零散 Cypher**：Planner 侧图谱仍只通过 `build_graph_context_for_planner1`；建图管线内部仍由 Cybereye4 `neo4j_sync` 执行（不在此仓库复制 SQL/Cypher）。
- **异常**：包装层捕获并返回结构化 `error` + `trace`，便于 HTTP/CI 消费。

## 许可证

包装层以本仓库为准；Cybereye4 本体遵循其原有许可证。
