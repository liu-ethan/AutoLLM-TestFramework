"""Pytest 配置与用例动态加载。

外部库：
- pytest: 提供钩子与参数化。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

import pytest

from src.utils.file_handler import read_json, read_yaml
from src.utils.logger import get_logger


def _collect_cases(cases_dir: Path) -> List[dict[str, Any]]:
    """
    扫描 data/test_cases 目录，收集所有 JSON 用例。

    返回：
    - List[dict]: 单条用例字典列表（支持文件内为 dict 或 list）
    """

    logger = get_logger(__name__)
    cases: List[dict[str, Any]] = []

    if not cases_dir.exists():
        logger.warning("Test cases directory not found: %s", cases_dir)
        return cases

    for path in sorted(cases_dir.glob("*.json")):
        data = read_json(str(path))
        if isinstance(data, list):
            cases.extend(data)
        elif isinstance(data, dict):
            cases.append(data)
        else:
            logger.warning("Unsupported case format in %s", path)

    return cases


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Pytest 钩子：动态参数化测试数据。

    当测试函数包含 case_data 参数时，
    自动将所有 JSON 用例注入生成测试。
    """

    if "case_data" not in metafunc.fixturenames:
        return

    settings = read_yaml("config/settings.yaml")
    cases_dir = Path(settings.get("paths", {}).get("test_cases_dir", "data/test_cases"))
    cases = _collect_cases(cases_dir)

    if not cases:
        # 没有用例时，显式生成空参数化
        metafunc.parametrize("case_data", [])
        return

    # 生成更易读的用例 ID
    ids = [case.get("name", f"case_{idx}") for idx, case in enumerate(cases)]
    metafunc.parametrize("case_data", cases, ids=ids)
