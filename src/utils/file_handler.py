"""结构化与文本的读写工具。

外部库：
- 配置解析库：解析与写入配置内容。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def read_yaml(path: str) -> Dict[str, Any]:
    """读取 YAML 配置并返回字典。"""

    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def read_json(path: str) -> Any:
    """读取 JSON 文件并返回原始对象。"""

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: str, data: Any) -> None:
    """将对象写入 JSON 文件，自动创建目录。"""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def read_text(path: str) -> str:
    """读取文本文件并返回完整字符串。"""

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def write_yaml(path: str, data: Dict[str, Any]) -> None:
    """将对象写入 YAML 文件，自动创建目录。"""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)
