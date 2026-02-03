from __future__ import annotations

import time
from typing import Optional

from openai import OpenAI

from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


class LLMClient:
    """
    统一封装 LLM 调用的客户端。

    设计目的：
    - 只关心“发问”和“收答”，不关心测试业务逻辑
    - 负责重试、超时等稳定性保障
    - 所有调用参数集中从配置文件读取，避免硬编码
    """

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        # 日志实例
        self._logger = get_logger(__name__)

        # 读取配置
        settings = read_yaml(settings_path)
        llm_settings = settings.get("llm", {})

        # LLM 连接与调用参数
        self.api_key = llm_settings.get("api_key")
        self.base_url = llm_settings.get("base_url")
        self.model = llm_settings.get("model")
        self.timeout_seconds = llm_settings.get("timeout_seconds", 60)
        self.max_retries = llm_settings.get("max_retries", 3)
        self.retry_backoff_seconds = llm_settings.get("retry_backoff_seconds", 2)

        # OpenAI SDK 客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat_completion(self, prompt: str, content: str) -> str:
        """
        向 LLM 发送对话请求并返回文本结果。

        参数说明：
        - prompt: 系统提示词（指导模型角色与输出格式）
        - content: 用户输入内容（原始接口文档或比较内容）

        返回：
        - LLM 返回的文本内容，若为空则返回空字符串
        """

        # 按 OpenAI Chat 模式组织消息
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ]

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # 发起请求
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    timeout=self.timeout_seconds,
                )
                # 只返回首条输出内容
                return response.choices[0].message.content or ""
            except Exception as exc:  # pragma: no cover
                # 失败记录并重试
                last_error = exc
                self._logger.warning(
                    "LLM request failed (attempt %s/%s): %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds)

        # 重试结束仍失败
        raise RuntimeError(f"LLM request failed after retries: {last_error}")
