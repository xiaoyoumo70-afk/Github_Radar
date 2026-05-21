"""JSON repair — extract and fix malformed LLM JSON output."""

from __future__ import annotations

import json
import re
from typing import Any

from .llm_client import LLMClient

REPAIR_PROMPT = """The following text was supposed to be valid JSON but is malformed.
Fix it to be valid JSON. Output ONLY the fixed JSON object, no surrounding text.

Malformed:
{raw}

Fixed JSON:"""


def _extract_json_block(raw: str) -> str:
    """Try to extract the outermost {...} block from raw text."""
    # Find first { and last }
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end > start:
        return raw[start:end + 1]
    return raw


def _fix_common_issues(text: str) -> str:
    """Apply common JSON syntax fixes."""
    # Remove trailing commas before closing brackets
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Fix unescaped newlines in strings (basic)
    return text


def repair_json(raw: str, llm: LLMClient | None = None) -> dict[str, Any]:
    """Attempt to extract and parse JSON from raw LLM output.

    Returns the parsed dict.
    Raises ValueError if all repair attempts fail.
    """
    # Attempt 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Attempt 2: extract {...} block
    extracted = _extract_json_block(raw)
    fixed = _fix_common_issues(extracted)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Attempt 3: LLM repair
    if llm is not None:
        prompt = REPAIR_PROMPT.format(raw=raw)
        repaired_text = llm.call(
            system_prompt="You are a JSON repair tool. Output only valid JSON.",
            user_prompt=prompt,
            temperature=0.0,
            max_tokens=4096,
        )
        try:
            return json.loads(repaired_text)
        except json.JSONDecodeError:
            try:
                return json.loads(_extract_json_block(repaired_text))
            except json.JSONDecodeError:
                pass

    # Attempt 4: return a degraded marker
    return {
        "_degraded": True,
        "_raw": raw[:2000],
        "repo_positioning": "JSON parse failed",
        "one_sentence_takeaway": "Analysis degraded — raw output saved",
    }
