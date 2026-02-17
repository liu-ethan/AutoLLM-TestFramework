"""命令行入口：生成并运行接口测试用例。

外部库：
- 参数解析库：解析命令行参数。
- 测试运行库：执行生成的测试用例。
- 子进程库：调用报告工具命令行生成报告。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

import pytest

from src.core.case_generator import CaseGenerator
from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


def _run_pytest(settings: dict) -> int:
    """运行 Pytest 并返回退出码。"""

    paths = settings.get("paths", {})
    results_dir = paths.get("allure_results_dir", "allure-results")
    os.makedirs(results_dir, exist_ok=True)

    return pytest.main(
        [
            "-q",
            "test_runner/test_executor.py",
            "--alluredir",
            results_dir,
        ]
    )


def _generate_allure_report(settings: dict) -> None:
    """
    调用报告工具命令行生成测试报告。

    注意：
    - 需要用户本地安装报告工具命令行
    - 生成的报告目录由 settings.yaml 控制
    """

    logger = get_logger(__name__)
    paths = settings.get("paths", {})
    results_dir = paths.get("allure_results_dir", "allure-results")
    report_dir = paths.get("allure_report_dir", "allure-report")

    try:
        subprocess.run(
            ["allure", "generate", results_dir, "-o", report_dir, "--clean"],
            check=True,
        )
        logger.info("Allure report generated at %s", report_dir)
    except FileNotFoundError:
        logger.warning("Allure CLI not found. Please install Allure to generate reports.")
    except subprocess.CalledProcessError as exc:
        logger.error("Allure report generation failed: %s", exc)


def main() -> int:
    """
    命令行主入口：支持三种模式。

    --mode generate：仅生成结构化用例
    --mode run：仅执行用例
    --mode all：生成 + 执行 + 生成测试报告
    """

    parser = argparse.ArgumentParser(description="AutoLLM Test Framework CLI")
    parser.add_argument("--mode", choices=["generate", "run", "all"], default="all")
    parser.add_argument("--doc", help="Optional document path to generate cases", default=None)
    args = parser.parse_args()

    logger = get_logger(__name__)
    settings = read_yaml("config/settings.yaml")

    if args.mode in {"generate", "all"}:
        logger.info("Generating test cases...")
        generator = CaseGenerator()
        generator.generate_cases(args.doc)

    exit_code = 0
    if args.mode in {"run", "all"}:
        logger.info("Running tests...")
        exit_code = _run_pytest(settings)

    if args.mode in {"run", "all"}:
        _generate_allure_report(settings)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
