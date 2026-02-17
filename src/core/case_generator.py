"""基于大模型的用例生成器。

外部库：
- 容错解析库：用于解析模型输出的结构化数据。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import json5

from src.agent_core.orchestration import AgentOrchestrator
from src.core.doc_parser import load_documents
from src.rag_core.doc_slicer import DocSlicer
from src.llm_client.openai_client import LLMClient
from src.utils.file_handler import read_yaml, write_json
from src.utils.global_vars import format_global_context, load_global_vars
from src.utils.json_parser import extract_json_payload
from src.utils.logger import get_logger


# 匹配代码块中的结构化输出
JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


class CaseGenerator:
    """
    智能用例生成器：将自然语言接口文档转为标准结构化用例。

    核心流程：
    1) 读取接口文档
    2) 使用 Prompt 组织请求
    3) 调用模型生成结构化用例
    4) 清洗并校验结构化内容
    5) 写入 data/test_cases
    """

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        # 初始化日志、配置、提示词与路径
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.prompts = read_yaml("config/prompt_templates.yaml")
        self.settings_path = settings_path
        self.raw_docs_dir = self.settings.get("paths", {}).get("raw_docs_dir", "data/raw_docs")
        self.test_cases_dir = Path(
            self.settings.get("paths", {}).get("test_cases_dir", "data/test_cases")
        )
        # 确保输出目录存在
        self.test_cases_dir.mkdir(parents=True, exist_ok=True)
        # 初始化 LLM 客户端与子模块配置
        self.llm_client = LLMClient(settings_path=settings_path, module_name="case_generator")
        self.rag_cfg = self.settings.get("rag", {})
        self.agent_cfg = self.settings.get("agentic", {})

    def generate_cases(self, doc_path: Optional[str] = None) -> List[dict[str, Any]]:
        """
        根据文档生成结构化用例并写入磁盘。

        参数：
        - doc_path: 指定单个文档路径（可选）

        返回：
        - 解析后的用例列表
        """
        # 读取文档内容（可选仅指定单个文档）
        content, paths = load_documents(self.raw_docs_dir, doc_path)
        if not content:
            raise ValueError("No document content found to generate cases.")
        # 读取并格式化全局变量上下文
        global_vars = load_global_vars(self.settings)
        global_context = format_global_context(global_vars)
        # 按配置决定是否启用 RAG 与 Agentic 循环
        rag_enabled = bool(self.rag_cfg.get("enabled", False))
        agentic_enabled = bool(self.agent_cfg.get("enabled", False))
        # 选择不同生成路径
        if rag_enabled:
            cases = self._generate_with_rag(content, global_context, agentic_enabled)
        else:
            # 获取生成提示词并发起调用
            generation_prompt = self.prompts.get("generation_prompt", "")
            payload = self._merge_context(global_context, content)
            llm_output = self.llm_client.chat_completion(generation_prompt, payload)
            json_payload = self._extract_json(llm_output)
            cases = self._normalize_cases(self._parse_json(json_payload))
        # 非按切片输出时，统一写入一个用例文件
        if not rag_enabled or not self.rag_cfg.get("output_per_chunk", False):
            # 输出文件命名：按文档名或合并策略
            filename = self._build_output_filename(paths, doc_path)
            output_path = self.test_cases_dir / filename
            write_json(str(output_path), cases)
            self._logger.info("Generated cases saved to %s", output_path)
        return cases

    def _generate_with_rag(
        self,
        content: str,
        global_context: str,
        agentic_enabled: bool,
    ) -> List[dict[str, Any]]:
        """检索增强切片 + 代理循环生成。"""
        # 切片文档并准备编排器
        header_levels = self.rag_cfg.get("header_levels", [1, 2])
        slicer = DocSlicer(header_levels=header_levels)
        chunks = slicer.slice_text(content)
        all_cases: List[dict[str, Any]] = []
        orchestrator = AgentOrchestrator(self.settings_path)
        # 遍历切片逐段生成用例
        for chunk in chunks:
            chunk_text = chunk.get("content", "")
            if not chunk_text.strip():
                continue
            if not self._is_relevant_chunk(chunk):
                self._logger.info("Skipping non-interface chunk: %s", chunk.get("title"))
                continue
            payload = self._merge_context(global_context, chunk_text)
            # 选择 Agentic 循环或直接生成
            if agentic_enabled:
                cases, feedback = orchestrator.run(payload)
                if feedback:
                    self._logger.info("Agent judge feedback: %s", feedback)
            else:
                generation_prompt = self.prompts.get("generation_prompt", "")
                llm_output = self.llm_client.chat_completion(generation_prompt, payload)
                json_payload = self._extract_json(llm_output)
                cases = self._parse_json(json_payload)
            # 归一化字段结构并按需写出切片文件
            cases = self._normalize_cases(cases)
            if self.rag_cfg.get("output_per_chunk", False):
                title = str(chunk.get("title") or "chunk")
                filename = self._safe_chunk_filename(title, chunk.get("index", 0))
                output_path = self.test_cases_dir / filename
                write_json(str(output_path), cases)
                self._logger.info("Generated cases saved to %s", output_path)
            all_cases.extend(cases)
        return all_cases

    def _is_relevant_chunk(self, chunk: dict[str, Any]) -> bool:
        """判断切片是否应参与用例生成。"""
        # 基于长度与关键字进行过滤
        cfg = self.rag_cfg or {}
        title = str(chunk.get("title") or "").strip()
        content = str(chunk.get("content") or "").strip()
        content_len = len(content)
        min_length = int(cfg.get("min_content_length", 200))
        if content_len < min_length:
            return False
        include_keywords = cfg.get("include_keywords") or []
        exclude_keywords = cfg.get("exclude_keywords") or []
        haystack = f"{title}\n{content}".lower()
        for keyword in exclude_keywords:
            if str(keyword).lower() in haystack:
                return False
        if include_keywords:
            return any(str(keyword).lower() in haystack for keyword in include_keywords)
        return True

    def _merge_context(self, global_context: str, content: str) -> str:
        # 将全局变量上下文拼接到文档内容前
        if not global_context:
            return content
        return f"{global_context}\n\n{content}".strip()

    def _safe_chunk_filename(self, title: str, index: int) -> str:
        # 生成安全的文件名
        cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", title).strip("_")
        if not cleaned:
            cleaned = f"chunk_{index}"
        return f"{cleaned}_cases.json"

    def _normalize_cases(self, cases: List[dict[str, Any]]) -> List[dict[str, Any]]:
        """将模型输出归一化为执行器期望的结构。"""
        # 过滤非 dict 元素并逐条归一化
        normalized: List[dict[str, Any]] = []
        for case in cases:
            if not isinstance(case, dict):
                continue
            normalized.append(self._normalize_case(case))
        return normalized

    def _normalize_case(self, case: dict[str, Any]) -> dict[str, Any]:
        """展开请求包裹结构，并映射常见字段别名。"""
        # 兼容 request 包裹结构
        request = case.get("request")
        if isinstance(request, dict):
            if "url" not in case and "url" in request:
                case["url"] = request.get("url")
            if "method" not in case and "method" in request:
                case["method"] = request.get("method")
            if "headers" not in case and "headers" in request:
                case["headers"] = request.get("headers")
            params = request.get("params")
            if params is None:
                params = request.get("query")
            if params is None:
                params = request.get("query_params")
            if "params" not in case and params is not None:
                case["params"] = params
            body = request.get("data")
            if body is None:
                body = request.get("body")
            if body is None:
                body = request.get("json")
            if "data" not in case and body is not None:
                case["data"] = body
            case.pop("request", None)
        # 兼容 body 字段别名
        if "data" not in case and "body" in case:
            case["data"] = case.pop("body")
        return case

    def _extract_json(self, llm_output: str) -> str:
        """
        从模型输出中提取纯结构化字符串。
        若存在 ```json 代码块则优先截取其内容。
        """
        # 优先截取 ```json``` 代码块
        match = JSON_BLOCK_RE.search(llm_output)
        if match:
            return match.group(1).strip()
        # 回退到通用 JSON 抽取逻辑
        return extract_json_payload(llm_output.strip())

    def _parse_json(self, payload: str) -> List[dict[str, Any]]:
        """
        将结构化字符串解析为 Python 对象。
        允许返回 dict 或 list，最终统一为 list。
        """
        # 先尝试严格 JSON，再兼容 JSON5
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
            return data # type: ignore
        self._logger.warning("Invalid JSON format for test cases")
        return []


    def _build_output_filename(self, paths: List[Path], doc_path: Optional[str]) -> str:
        """
        输出文件命名策略：
        - 指定文档：<doc>_cases.json
        - 单一文档：<doc>_cases.json
        - 多文档合并：combined_<n>_cases.json
        - 无文档时以时间戳兜底
        """
        # 按输入文档/合并策略命名
        if doc_path:
            return f"{Path(doc_path).stem}_cases.json"
        if paths:
            if len(paths) == 1:
                return f"{paths[0].stem}_cases.json"
            return f"combined_{len(paths)}_cases.json"
        # 兜底使用时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"cases_{timestamp}.json"
