"""Agentic 编排循环：协调生成与评审。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.agent_core.generator import AgentGenerator
from src.agent_core.judge import AgentJudge
from src.utils.file_handler import read_yaml
from src.utils.logger import get_logger


class AgentOrchestrator:
    """在重试循环中协调生成与评审。"""

    def __init__(
        self,
        settings_path: str = "config/settings.yaml",
        module_name: str = "agentic_loop",
    ) -> None:
        # 初始化日志、配置与生成/评审组件
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.agent_cfg = self.settings.get("agentic", {})
        self.generator = AgentGenerator(settings_path=settings_path)
        self.judge = AgentJudge(settings_path=settings_path)
        # 当前模块名用于配置覆盖
        self.module_name = module_name

    def run(self, chunk_text: str) -> Tuple[List[Dict[str, Any]], str]:
        """执行单个切片的 Agentic 循环并返回（用例列表，评审反馈）。"""
        # 解析最大循环次数与是否快速失败
        max_rounds = self._resolve_max_rounds()
        fail_fast = bool(self.agent_cfg.get("fail_fast", False))
        # 反馈在轮次间传递，用于引导后续生成
        feedback: Optional[str] = None
        cases: List[Dict[str, Any]] = []
        last_feedback = ""

        for round_idx in range(1, max_rounds + 1):
            # 每轮：生成 -> 评审 -> 根据结果决定是否继续
            self._logger.info("Agentic round %s/%s", round_idx, max_rounds)
            cases = self.generator.generate(chunk_text, feedback=feedback)
            passed, review = self.judge.review(chunk_text, cases)
            last_feedback = review
            if passed:
                # 评审通过直接返回
                return cases, review
            # 评审未通过则将反馈带入下一轮
            feedback = review
            if fail_fast:
                # fail_fast 模式下首轮失败即退出
                break
        # 轮次用尽或快速失败时返回最后一轮结果
        return cases, last_feedback

    def _resolve_max_rounds(self) -> int:
        """解析最大循环次数，支持按模块覆盖。"""
        # 默认轮次来自 agentic.max_rounds
        default_rounds = int(self.agent_cfg.get("max_rounds", 2))
        # 支持按模块名或 default 覆盖
        overrides = self.agent_cfg.get("max_rounds_by_module", {})
        if isinstance(overrides, dict):
            if self.module_name in overrides:
                return int(overrides.get(self.module_name, default_rounds))
            if "default" in overrides:
                return int(overrides.get("default", default_rounds))
        # 未命中覆盖则回退默认值
        return default_rounds
