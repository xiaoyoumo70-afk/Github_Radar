"""Structure pass — architectural understanding from directory tree."""

from __future__ import annotations

from ..models.analysis import StructureAnalysis
from ..models.repo import RepoRef
from ..storage.artifacts import read_json, write_json
from ..storage.paths import RepoPaths
from .json_repair import repair_json
from .llm_client import LLMClient

STRUCTURE_PROMPT = """你是一个代码架构分析助手。

根据以下仓库的目录结构和已有分析，产出结构理解。

## 项目
- 名称：{repo_name}
- 定位：{positioning}

## 目录结构
- 顶层目录：{top_dirs}
- 配置文件：{configs}
- 文档路径：{docs}
- 可能的入口：{entrypoints}
- 测试目录：{tests}

## 已有分析
{snapshot_summary}

## 输出要求
严格输出 JSON：

{{
  "entrypoints": ["路径1", "路径2"],
  "major_modules": ["模块1", "模块2"],
  "architecture_summary": "架构概述（≤200字）",
  "learning_order": ["第一步", "第二步"],
  "files_to_read_next": ["文件路径1", "文件路径2"]
}}

major_modules 最多 8 项。files_to_read_next 必须是目录树中真实存在的路径。"""


def run_structure_pass(
    ref: RepoRef,
    paths: RepoPaths,
    llm: LLMClient,
    force: bool = False,
) -> StructureAnalysis:
    """Analyze repo structure from tree scan."""
    if not force and paths.structure_file.exists():
        return StructureAnalysis.model_validate(read_json(paths.structure_file))

    tree = read_json(paths.tree_file)
    snapshot = read_json(paths.snapshot_file)

    prompt = STRUCTURE_PROMPT.format(
        repo_name=ref.full_name,
        positioning=snapshot.get("repo_positioning", "未知"),
        top_dirs=", ".join(tree.get("top_level_dirs", [])),
        configs=", ".join(tree.get("config_files", [])[:5]),
        docs=", ".join(tree.get("doc_paths", [])[:8]),
        entrypoints=", ".join(tree.get("entrypoint_paths", [])[:8]),
        tests=", ".join(tree.get("test_paths", [])[:5]),
        snapshot_summary=str(snapshot)[:1500],
    )

    raw = llm.call(
        system_prompt="你是一个代码架构分析助手，输出严格 JSON。",
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=2048,
    )

    data = repair_json(raw, llm)
    analysis = StructureAnalysis.model_validate(data)
    write_json(paths.structure_file, analysis.model_dump())
    return analysis
