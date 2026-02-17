"""全局变量加载与格式化。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


def load_global_vars(settings: Dict[str, Any]) -> Dict[str, Any]:
    """在启用时从 config/global_vars.yaml 读取全局变量。"""

    logger = get_logger(__name__)
    cfg = settings.get("global_vars", {})
    if not cfg.get("enabled", False):
        return {}

    path = cfg.get("path", "config/global_vars.yaml")
    if not Path(path).exists():
        logger.warning("Global vars file not found: %s", path)
        return {}

    return read_yaml(path) or {}


def format_global_context(global_vars: Dict[str, Any]) -> str:
    """将全局变量格式化为 Prompt 可用的上下文块。"""

    if not global_vars:
        return ""

    dumped = yaml.safe_dump(
        global_vars,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"Global Vars:\n{dumped}".strip()
