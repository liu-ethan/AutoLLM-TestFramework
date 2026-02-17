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


# 捕获 ```json ... ``` 代码块中的 JSON 内容
_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


class AgentGenerator:
    """生成 Agent：基于切片内容生成测试用例。"""

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        # 初始化日志、配置、提示词与 LLM 客户端
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
        # 选择提示词模板，优先 agent_generation_prompt
        prompt = self.prompts.get("agent_generation_prompt") or self.prompts.get(
            "generation_prompt", ""
        )
        # 拼接切片内容与可选的评审反馈
        content = chunk_text
        if feedback:
            content = f"{chunk_text}\n\n[Judge Feedback]\n{feedback}".strip()
        # 调用 LLM 生成测试用例
        llm_output = self.llm_client.chat_completion(prompt, content)
        # 提取输出中的 JSON 载荷
        payload = self._extract_json(llm_output)
        # 解析 JSON 为统一的用例列表
        return self._parse_json(payload)

    def _extract_json(self, llm_output: str) -> str:
        # 优先从 ```json``` 代码块提取
        match = _JSON_BLOCK_RE.search(llm_output)
        if match:
            return match.group(1).strip()
        # 回退到通用 JSON 抽取逻辑
        return extract_json_payload(llm_output.strip())

    def _parse_json(self, payload: str) -> List[Dict[str, Any]]:
        # 尝试标准 JSON 解析
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            # 兼容 JSON5（宽松语法）
            try:
                data = json5.loads(payload)
            except Exception as exc:
                # 解析失败则返回空列表
                self._logger.warning("Failed to parse JSON payload: %s", exc)
                return []
        # 统一输出为 List[Dict]
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data # type: ignore
        # 不支持的结构直接告警并返回空
        self._logger.warning("Agent generator returned unsupported JSON payload")
        return []

