"""Agentic 评审器：校验生成的测试用例。"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.llm_client.openai_client import LLMClient
from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


class AgentJudge:
    """评审 Agent：检查用例质量并返回通过/不通过。"""

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        # 初始化日志、配置、提示词与 LLM 客户端
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.prompts = read_yaml("config/prompt_templates.yaml")
        self.llm_client = LLMClient(settings_path=settings_path, module_name="agent_judge")

    def review(self, chunk_text: str, cases: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """评审生成用例并返回（是否通过，反馈文本）。"""
        # 选择评审提示词模板，优先 agent_judge_prompt
        prompt = self.prompts.get("agent_judge_prompt") or self.prompts.get(
            "judge_prompt", ""
        )
        # 拼接文档切片与生成用例作为评审输入
        content = f"[Document Chunk]\n{chunk_text}\n\n[Generated Cases]\n{cases}"
        # 调用 LLM 获取评审结果
        result = self.llm_client.chat_completion(prompt, content).strip()
        normalized = result.lower() # 将结果转换为小写以便判定
        # 兼容大小写，判定通过或失败
        if "pass" in normalized and "fail" not in normalized:
            return True, result
        if "fail" in normalized:
            return False, result
        # 未命中关键字则告警并视为失败
        self._logger.warning("Agent judge returned unexpected value: %s", result)
        return False, result
