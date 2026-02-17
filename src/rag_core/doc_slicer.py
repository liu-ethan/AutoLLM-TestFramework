"""检索增强预处理的标记文档切片器。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

try:  # 可选依赖
    from langchain.text_splitter import MarkdownHeaderTextSplitter # type: ignore

    _HAS_LANGCHAIN = True
except Exception:
    MarkdownHeaderTextSplitter = None
    _HAS_LANGCHAIN = False


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")


class DocSlicer:
    """按标题层级切分标记文本。"""

    def __init__(self, header_levels: Optional[List[int]] = None) -> None:
        self._logger = get_logger(__name__)
        self.header_levels = header_levels or [1, 2]

    def slice_text(self, text: str) -> List[Dict[str, Any]]:
        """按标题切分文本为多个切片。"""

        if _HAS_LANGCHAIN:
            return self._slice_with_langchain(text)
        return self._slice_with_regex(text)

    def _slice_with_langchain(self, text: str) -> List[Dict[str, Any]]:
        """可用时使用 LangChain 的 MarkdownHeaderTextSplitter。"""

        headers = [("#" * level, f"H{level}") for level in self.header_levels]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers) # type: ignore
        docs = splitter.split_text(text)
        chunks: List[Dict[str, Any]] = []
        for idx, doc in enumerate(docs):
            title = self._pick_header_title(doc.metadata)
            chunks.append(
                {
                    "index": idx,
                    "title": title,
                    "content": doc.page_content,
                    "metadata": dict(doc.metadata),
                }
            )
        return chunks

    def _slice_with_regex(self, text: str) -> List[Dict[str, Any]]:
        """基于正则的兜底切片逻辑。"""

        lines = text.splitlines()
        chunks: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {"title": "", "level": None, "lines": []}

        def flush() -> None:
            if not current["lines"]:
                return
            content = "\n".join(current["lines"]).strip()
            if content:
                chunks.append(
                    {
                        "index": len(chunks),
                        "title": current["title"] or f"chunk_{len(chunks)}",
                        "content": content,
                        "metadata": {"level": current["level"]},
                    }
                )
            current["lines"] = []

        for line in lines:
            match = _HEADER_RE.match(line.strip())
            if match:
                level = len(match.group(1))
                if level in self.header_levels:
                    flush()
                    current["title"] = match.group(2).strip()
                    current["level"] = level
                    current["lines"].append(line)
                    continue
            current["lines"].append(line)

        flush()
        if not chunks:
            chunks.append({"index": 0, "title": "chunk_0", "content": text, "metadata": {}})
        return chunks

    def _pick_header_title(self, metadata: Dict[str, Any]) -> str:
        """从 LangChain 元数据中选取可用标题。"""

        for level in self.header_levels:
            key = f"H{level}"
            if key in metadata:
                return str(metadata[key])
        for value in metadata.values():
            if value:
                return str(value)
        return ""
