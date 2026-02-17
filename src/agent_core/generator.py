"""Agentic 生成器：用于生成测试用例。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import json5

from src.llm_client.openai_client import LLMClient
from src.utils.file_handler import read_yaml
from src.utils.json_parser import extract_json_payload
from src.utils.logger import get_logger


_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


class AgentGenerator:
    """生成 Agent：基于切片内容生成测试用例。"""

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.prompts = read_yaml("config/prompt_templates.yaml")
        self.llm_client = LLMClient(settings_path=settings_path, module_name="agent_generator")

    def generate(
        self,
        chunk_text: str,
        feedback: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """为单个切片生成测试用例，可选包含评审反馈。"""

        prompt = self.prompts.get("agent_generation_prompt") or self.prompts.get(
            "generation_prompt", ""
        )
        content = chunk_text
        if feedback:
            content = f"{chunk_text}\n\n[Judge Feedback]\n{feedback}".strip()

        llm_output = self.llm_client.chat_completion(prompt, content)
        payload = self._extract_json(llm_output)
        return self._parse_json(payload)

    def _extract_json(self, llm_output: str) -> str:
        match = _JSON_BLOCK_RE.search(llm_output)
        if match:
            return match.group(1).strip()
        return extract_json_payload(llm_output.strip())

    def _parse_json(self, payload: str) -> List[Dict[str, Any]]:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            try:
                data = json5.loads(payload)
            except Exception as exc:
                self._logger.warning("Failed to parse JSON payload: %s", exc)
                return []

        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        self._logger.warning("Agent generator returned unsupported JSON payload")
        return []

