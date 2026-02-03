from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from src.utils.file_handler import read_text
from src.utils.logger import get_logger


def load_documents(raw_docs_dir: str, doc_path: Optional[str] = None) -> Tuple[str, List[Path]]:
    """
    读取接口文档内容。

    参数说明：
    - raw_docs_dir: 默认原始文档目录，读取其中全部 .md/.txt
    - doc_path: 若指定则只读取该文件

    返回：
    - combined: 文档拼接后的完整文本
    - paths: 实际读取到的文件路径列表
    """

    logger = get_logger(__name__)
    paths: List[Path] = []
    raw_dir = Path(raw_docs_dir)

    # 指定单文件
    if doc_path:
        target = Path(doc_path)
        if not target.exists():
            raise FileNotFoundError(f"Document not found: {target}")
        paths = [target]
    else:
        # 读取目录下所有支持格式
        if not raw_dir.exists():
            logger.warning("Raw docs directory not found: %s", raw_dir)
            return "", []
        paths = sorted([p for p in raw_dir.iterdir() if p.suffix in {".md", ".txt"}])

    # 合并内容供 LLM 一次性处理
    contents = []
    for path in paths:
        contents.append(read_text(str(path)))

    combined = "\n\n".join(contents).strip()
    return combined, paths
