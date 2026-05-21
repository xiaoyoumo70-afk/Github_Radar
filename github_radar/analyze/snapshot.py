"""Snapshot analysis — quick project assessment."""

from __future__ import annotations

from ..models.analysis import SnapshotAnalysis
from ..models.repo import RepoRef
from ..storage.artifacts import read_json, read_text, write_json
from ..storage.paths import RepoPaths
from .json_repair import repair_json
from .llm_client import LLMClient

SNAPSHOT_PROMPT = """你是一个开源项目分析助手。

根据以下 repo 基本信息，给出评审摘要。不要猜测，不确定的写"未知"。

## 项目信息
- 名称：{repo_name}
- 描述：{description}
- 语言：{language}
- Topics：{topics}
- Stars：{stars}

## README 摘要（前 3000 字）
{readme_head}

## 输出要求
严格输出 JSON，不要外围文本：

{{
  "repo_positioning": "一句话定位（≤80字）",
  "primary_use_cases": ["用例1", "用例2"],
  "tech_stack": ["技术1", "技术2"],
  "why_interesting": ["关注理由1", "关注理由2"],
  "worth_deep_reading": true,
  "open_questions": ["问题1", "问题2"]
}}

每个字符串字段不超过 200 字。worth_deep_reading 为 true 表示值得继续深入分析。"""


def run_snapshot(
    ref: RepoRef,
    paths: RepoPaths,
    llm: LLMClient,
    force: bool = False,
) -> SnapshotAnalysis:
    """Run quick assessment pass on a repo."""
    if not force and paths.snapshot_file.exists():
        return SnapshotAnalysis.model_validate(read_json(paths.snapshot_file))

    metadata = read_json(paths.metadata_file)
    readme_text = ""
    if paths.readme_file.exists():
        readme_text = read_text(paths.readme_file)[:3000]

    prompt = SNAPSHOT_PROMPT.format(
        repo_name=ref.full_name,
        description=metadata.get("description", "未知"),
        language=metadata.get("language", "未知"),
        topics=", ".join(metadata.get("topics", [])),
        stars=metadata.get("stars", "未知"),
        readme_head=readme_text,
    )

    raw = llm.call(
        system_prompt="你是一个开源项目分析助手，输出严格 JSON。",
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=2048,
    )

    data = repair_json(raw, llm)
    analysis = SnapshotAnalysis.model_validate(data)
    write_json(paths.snapshot_file, analysis.model_dump())
    return analysis
