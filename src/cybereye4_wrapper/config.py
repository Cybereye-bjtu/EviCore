"""Wrapper-local configuration (does not modify the Cybereye4 tree)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _strip_or_none(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = v.strip()
    return s if s else None


@dataclass(frozen=True)
class WrapperSettings:
    """Resolved settings for the wrapper process."""

    cybereye_src_root: str
    llm_model: str
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]


def get_settings() -> WrapperSettings:
    root = os.environ.get("CYBEREYE_SRC_ROOT", "").strip()
    if not root:
        raise ValueError(
            "CYBEREYE_SRC_ROOT is not set. Point it to the Cybereye4 project directory "
            "(e.g. /home/user/cybereye4). See .env.example."
        )
    model = os.environ.get("CYBEREYE_LLM_MODEL", "gemini-2.5-flash").strip()
    api_key = _strip_or_none(os.environ.get("OPENAI_API_KEY"))
    base_url = _strip_or_none(os.environ.get("OPENAI_BASE_URL"))
    return WrapperSettings(
        cybereye_src_root=os.path.abspath(os.path.expanduser(root)),
        llm_model=model or "gemini-2.5-flash",
        openai_api_key=api_key,
        openai_base_url=base_url,
    )
