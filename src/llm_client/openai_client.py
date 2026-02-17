"""兼容接口的对话调用封装。

外部库：
- 模型调用库：官方客户端，用于模型调用。
"""

from __future__ import annotations

import time
from typing import Optional

from openai import OpenAI

from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


class LLMClient:
    """
    统一封装大模型调用的客户端。

    设计目的：
    - 只关心“发问”和“收答”，不关心测试业务逻辑
    - 负责重试、超时等稳定性保障
    - 所有调用参数集中从配置文件读取，避免硬编码
    """

    def __init__(
        self,
        settings_path: str = "config/settings.yaml",
        module_name: Optional[str] = None,
    ) -> None:
        # 日志实例
        self._logger = get_logger(__name__)

        # 读取配置
        settings = read_yaml(settings_path)
        llm_settings = settings.get("llm", {})
        profiles = settings.get("llm_profiles", {})
        module_map = settings.get("llm_modules", {})

        resolved = self._resolve_module_settings(
            llm_settings, profiles, module_map, module_name
        )

        # 大模型连接与调用参数
        self.api_key = resolved.get("api_key")
        self.base_url = resolved.get("base_url")
        self.model = resolved.get("model")
        self.timeout_seconds = resolved.get("timeout_seconds", 60)
        self.max_retries = resolved.get("max_retries", 3)
        self.retry_backoff_seconds = resolved.get("retry_backoff_seconds", 2)

        # 兼容接口客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat_completion(self, prompt: str, content: str) -> str:
        """
        向大模型发送对话请求并返回文本结果。

        参数说明：
        - prompt：系统提示词（指导模型角色与输出格式）
        - content：用户输入内容（原始接口文档或比较内容）

        返回：
        - 模型返回的文本内容，若为空则返回空字符串
        """

        # 按对话格式组织消息
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
            except Exception as exc:
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

    def _resolve_module_settings(
        self,
        base: dict,
        profiles: dict,
        module_map: dict,
        module_name: Optional[str],
    ) -> dict:
        """按模块与档位配置解析最终模型参数。"""

        resolved = dict(base)
        if not module_map:
            return resolved

        selected = None
        if module_name and module_name in module_map:
            selected = module_map.get(module_name)
        elif "default" in module_map:
            selected = module_map.get("default")

        if isinstance(selected, dict):
            resolved.update(selected)
            return resolved

        if isinstance(selected, str):
            profile = profiles.get(selected)
            if isinstance(profile, dict):
                resolved.update(profile)
                return resolved
            resolved["model"] = selected

        return resolved
