from __future__ import annotations

from typing import Any, Dict

import allure
import pytest
import requests

from src.core.ai_judge import AIJudge
from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


def test_api_case(case_data: Dict[str, Any]) -> None:
    """
    用例执行入口（Pytest 会为每条 JSON 用例生成一次调用）。

    流程：
    1) 从 case_data 解析请求信息
    2) 动态化 Allure 标注
    3) 发起 HTTP 请求
    4) 调用 AIJudge 进行断言
    """

    logger = get_logger(__name__)
    settings = read_yaml("config/settings.yaml")
    exec_cfg = settings.get("execution", {})

    # 2) 动态化 Allure 标注
    module_name = case_data.get("module")
    story_name = case_data.get("story")
    case_title = case_data.get("title") or case_data.get("name")
    if module_name:
        allure.dynamic.feature(module_name)
    if story_name:
        allure.dynamic.story(story_name)
    if case_title:
        allure.dynamic.title(case_title)

    # 3) 解析用例字段
    url = case_data.get("url")
    method = case_data.get("method", "GET")
    headers = case_data.get("headers") or {}
    params = case_data.get("params") or {}
    payload = case_data.get("data") or {}

    if not url:
        pytest.skip("Case missing URL")

    # 4) 发起请求
    logger.info("Executing case: %s %s", method, url)
    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=payload,
        timeout=exec_cfg.get("request_timeout_seconds", 30),
        verify=exec_cfg.get("verify_ssl", True),
    )

    # 5) 断言配置（用例优先于全局配置）
    assert_type = case_data.get("assert_type", exec_cfg.get("default_assert_type", "semantic_match"))
    use_ai = case_data.get("use_ai_assertion", exec_cfg.get("use_ai_assertion", True))

    judge = AIJudge()
    expected = case_data.get("expected", "")
    actual = response.text

    # 6) 执行断言
    assert judge.verify(expected, actual, assert_type=assert_type, use_ai_assertion=use_ai)
