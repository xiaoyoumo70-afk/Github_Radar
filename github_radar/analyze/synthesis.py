"""Final synthesis — comprehensive analysis for Obsidian output."""

from __future__ import annotations

from ..models.analysis import FinalSynthesis
from ..models.repo import RepoRef
from ..storage.artifacts import read_json, write_json
from ..storage.paths import RepoPaths
from .json_repair import repair_json
from .llm_client import LLMClient

SYNTHESIS_PROMPT = """你是一个开源项目研究报告撰写助手。

根据以下已有分析，生成最终综合报告。

## 项目
- 名称：{repo_name}
- 定位：{positioning}

## 快照分析
{snapshot}

## 结构分析
{structure}

## 输出要求
严格输出 JSON：

{{
  "one_sentence_takeaway": "一句话判断（≤80字）",
  "detailed_summary": "详细总结（≤800字）",
  "key_innovations": ["创新点1", "创新点2"],
  "limitations": ["局限1", "局限2"],
  "related_projects": ["相关项目1", "相关项目2"],
  "follow_up_questions": ["值得跟进的问题1", "问题2"],
  "recommended_action": "deep-study / bookmark / skip",
  "obsidian_tags": ["tag1", "tag2"]
}}

related_projects 只列 README 中明确提及或有明确对比关系的项目。obsidian_tags 最多 8 个。"""


def run_synthesis(
    ref: RepoRef,
    paths: RepoPaths,
    llm: LLMClient,
    force: bool = False,
) -> FinalSynthesis:
    """Generate final synthesis from all prior analyses."""
    if not force and paths.synthesis_file.exists():
        return FinalSynthesis.model_validate(read_json(paths.synthesis_file))

    snapshot = read_json(paths.snapshot_file)
    structure = read_json(paths.structure_file)

    prompt = SYNTHESIS_PROMPT.format(
        repo_name=ref.full_name,
        positioning=snapshot.get("repo_positioning", "未知"),
        snapshot=str(snapshot)[:2000],
        structure=str(structure)[:1500],
    )

    raw = llm.call(
        system_prompt="你是一个开源项目研究报告撰写助手，输出严格 JSON。",
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=4096,
    )

    data = repair_json(raw, llm)
    analysis = FinalSynthesis.model_validate(data)
    write_json(paths.synthesis_file, analysis.model_dump())
    return analysis
