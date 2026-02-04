from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import json5

from src.core.doc_parser import load_documents
from src.llm_client.openai_client import LLMClient
from src.utils.file_handler import read_yaml, write_json
from src.utils.logger import get_logger


# 匹配 Markdown 代码块中的 JSON 输出
JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


class CaseGenerator:
    """
    智能用例生成器：将自然语言接口文档转为标准 JSON 用例。

    核心流程：
    1) 读取接口文档
    2) 使用 Prompt 组织请求
    3) 调用 LLM 生成 JSON 用例
    4) 清洗并校验 JSON
    5) 写入 data/test_cases
    """

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.prompts = read_yaml("config/prompt_templates.yaml")
        self.raw_docs_dir = self.settings.get("paths", {}).get("raw_docs_dir", "data/raw_docs")
        self.test_cases_dir = Path(
            self.settings.get("paths", {}).get("test_cases_dir", "data/test_cases")
        )
        self.test_cases_dir.mkdir(parents=True, exist_ok=True)
        self.llm_client = LLMClient(settings_path=settings_path)

    def generate_cases(self, doc_path: Optional[str] = None) -> List[dict[str, Any]]:
        """
        根据文档生成 JSON 用例并写入磁盘。

        参数：
        - doc_path: 指定单个文档路径（可选）

        返回：
        - 解析后的用例列表
        """

        content, paths = load_documents(self.raw_docs_dir, doc_path)
        if not content:
            raise ValueError("No document content found to generate cases.")

        # 获取生成提示词并发起调用
        generation_prompt = self.prompts.get("generation_prompt", "")
        llm_output = self.llm_client.chat_completion(generation_prompt, content)

        # LLM 可能返回 Markdown 代码块，先提取 JSON 部分
        json_payload = self._extract_json(llm_output)
        cases = self._parse_json(json_payload)

        # 输出文件命名：按文档名或合并策略
        filename = self._build_output_filename(paths, doc_path)
        output_path = self.test_cases_dir / filename
        write_json(str(output_path), cases)
        self._logger.info("Generated cases saved to %s", output_path)
        return cases

    def _extract_json(self, llm_output: str) -> str:
        """
        从 LLM 输出中提取纯 JSON 字符串。
        若存在 ```json 代码块则优先截取其内容。
        """

        match = JSON_BLOCK_RE.search(llm_output)
        if match:
            return match.group(1).strip()
        return llm_output.strip()

    def _parse_json(self, payload: str) -> List[dict[str, Any]]:
        """
        将 JSON 字符串解析为 Python 对象。
        允许返回 dict 或 list，最终统一为 list。
        """

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = json5.loads(payload)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        raise ValueError("Invalid JSON format for test cases.")

    def _build_output_filename(self, paths: List[Path], doc_path: Optional[str]) -> str:
        """
        输出文件命名策略：
        - 指定文档：<doc>_cases.json
        - 单一文档：<doc>_cases.json
        - 多文档合并：combined_<n>_cases.json
        - 无文档时以时间戳兜底
        """

        if doc_path:
            return f"{Path(doc_path).stem}_cases.json"
        if paths:
            if len(paths) == 1:
                return f"{paths[0].stem}_cases.json"
            return f"combined_{len(paths)}_cases.json"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"cases_{timestamp}.json"
