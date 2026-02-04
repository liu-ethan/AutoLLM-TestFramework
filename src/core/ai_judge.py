from __future__ import annotations

import json
from typing import Any

from src.llm_client.openai_client import LLMClient
from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


class AIJudge:
    """
    AI 语义校验模块。

    目的：
    - 对复杂断言（如模糊匹配、语义一致性）进行自动判断
    - 与传统 exact_match 断言并行，按用例/配置决定策略
    """

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.prompts = read_yaml("config/prompt_templates.yaml")
        self.llm_client = LLMClient(settings_path=settings_path)

    def verify(
        self,
        expected_result: Any,
        actual_response: Any,
        assert_type: str = "semantic_match",
        use_ai_assertion: bool = True,
    ) -> bool:
        """
        断言入口。

        参数：
        - expected_result: 预期结果（文本或结构）
        - actual_response: 实际响应（文本或结构）
        - assert_type: exact_match 或 semantic_match
        - use_ai_assertion: 是否启用 AI 判定

        返回：
        - True: 断言通过
        - False: 断言失败
        """

        # 1) 精确匹配
        if assert_type == "exact_match":
            return str(expected_result).strip() == str(actual_response).strip()

        # 2) 语义匹配但禁用 AI：使用轻量启发式规则
        if not use_ai_assertion:
            return self._heuristic_match(expected_result, actual_response)

        # 3) 语义匹配：调用 LLM
        prompt = self.prompts.get("judge_prompt", "")
        content = f"A(预期): {expected_result}\nB(实际): {actual_response}"
        result = self.llm_client.chat_completion(prompt, content)

        # 4) 解析结果：只接受 True/False
        normalized = result.strip().lower()
        if "true" in normalized:
            return True
        if "false" in normalized:
            return False

        # 5) 兜底：异常输出视为失败，并记录日志
        self._logger.warning("AI judge returned unexpected value: %s", result)
        return False

    def _heuristic_match(self, expected_result: Any, actual_response: Any) -> bool:
        """
        无 AI 时的轻量语义匹配：
        - 优先解析 JSON 响应中的 msg/message 字段
        - 根据预期文本中的关键短语进行包含判断
        """

        expected_text = str(expected_result).strip()
        actual_text = str(actual_response).strip()

        msg = ""
        try:
            parsed = json.loads(actual_text)
            if isinstance(parsed, dict):
                msg = str(parsed.get("msg") or parsed.get("message") or "").strip()
        except Exception:  # pragma: no cover
            msg = ""

        key_phrase = ""
        if "：" in expected_text:
            key_phrase = expected_text.split("：")[-1].strip(" 。")
        elif ":" in expected_text:
            key_phrase = expected_text.split(":")[-1].strip(" .")

        if msg:
            if key_phrase:
                if key_phrase in msg or msg in key_phrase:
                    return True
            if expected_text.startswith("成功"):
                return "成功" in msg
            if expected_text.startswith("失败"):
                return "失败" in msg
            if msg in expected_text:
                return True

        # 无 msg 或无法匹配时，退化为文本包含
        return expected_text in actual_text
