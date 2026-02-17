"""Agentic 评审器：校验生成的测试用例。"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.llm_client.openai_client import LLMClient
from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


class AgentJudge:
    """评审 Agent：检查用例质量并返回通过/不通过。"""

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.prompts = read_yaml("config/prompt_templates.yaml")
        self.llm_client = LLMClient(settings_path=settings_path, module_name="agent_judge")

    def review(self, chunk_text: str, cases: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """评审生成用例并返回（是否通过，反馈文本）。"""

        prompt = self.prompts.get("agent_judge_prompt") or self.prompts.get(
            "judge_prompt", ""
        )
        content = f"[Document Chunk]\n{chunk_text}\n\n[Generated Cases]\n{cases}"
        result = self.llm_client.chat_completion(prompt, content).strip()
        normalized = result.lower()

        if "pass" in normalized and "fail" not in normalized:
            return True, result
        if "fail" in normalized:
            return False, result

        self._logger.warning("Agent judge returned unexpected value: %s", result)
        return False, result
