"""Structured analysis output schemas for LLM consumption."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SnapshotAnalysis(BaseModel):
    """Phase 1: quick assessment — worth reading deeper?"""

    repo_positioning: str = Field(
        description="One-sentence positioning of the project"
    )
    primary_use_cases: list[str] = Field(
        default_factory=list, description="2-4 primary use cases"
    )
    tech_stack: list[str] = Field(
        default_factory=list, description="Key technologies used"
    )
    why_interesting: list[str] = Field(
        default_factory=list, description="Why this project is notable right now"
    )
    worth_deep_reading: bool = Field(
        description="Whether to continue with structure/deep analysis"
    )
    open_questions: list[str] = Field(
        default_factory=list, description="Questions for deeper reading"
    )


class StructureAnalysis(BaseModel):
    """Phase 2: structural understanding from tree scan."""

    entrypoints: list[str] = Field(
        default_factory=list, description="Main entry points"
    )
    major_modules: list[str] = Field(
        default_factory=list, description="Key modules/packages (max 8)"
    )
    architecture_summary: str = Field(description="Summary of project architecture")
    learning_order: list[str] = Field(
        default_factory=list, description="Recommended reading order"
    )
    files_to_read_next: list[str] = Field(
        default_factory=list, description="Files to read in focused pass"
    )


class FinalSynthesis(BaseModel):
    """Phase 3: final synthesis for Obsidian output."""

    one_sentence_takeaway: str = Field(
        description="Single sentence takeaway (≤80 chars)"
    )
    detailed_summary: str = Field(
        description="Detailed summary (≤800 chars)"
    )
    key_innovations: list[str] = Field(
        default_factory=list, description="Key innovations or unique aspects"
    )
    limitations: list[str] = Field(
        default_factory=list, description="Known limitations or risks"
    )
    related_projects: list[str] = Field(
        default_factory=list,
        description="Related projects mentioned in README or model knowledge",
    )
    follow_up_questions: list[str] = Field(
        default_factory=list, description="Questions worth investigating further"
    )
    recommended_action: str = Field(
        description="Recommended action: deep-study / bookmark / skip"
    )
    obsidian_tags: list[str] = Field(
        default_factory=list, description="Suggested Obsidian tags (max 8)"
    )
