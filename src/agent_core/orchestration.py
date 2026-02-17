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
        self._logger = get_logger(__name__)
        self.settings = read_yaml(settings_path)
        self.agent_cfg = self.settings.get("agentic", {})
        self.generator = AgentGenerator(settings_path=settings_path)
        self.judge = AgentJudge(settings_path=settings_path)
        self.module_name = module_name

    def run(self, chunk_text: str) -> Tuple[List[Dict[str, Any]], str]:
        """执行单个切片的 Agentic 循环并返回（用例列表，评审反馈）。"""

        max_rounds = self._resolve_max_rounds()
        fail_fast = bool(self.agent_cfg.get("fail_fast", False))
        feedback: Optional[str] = None
        cases: List[Dict[str, Any]] = []
        last_feedback = ""

        for round_idx in range(1, max_rounds + 1):
            self._logger.info("Agentic round %s/%s", round_idx, max_rounds)
            cases = self.generator.generate(chunk_text, feedback=feedback)
            passed, review = self.judge.review(chunk_text, cases)
            last_feedback = review
            if passed:
                return cases, review
            feedback = review
            if fail_fast:
                break

        return cases, last_feedback

    def _resolve_max_rounds(self) -> int:
        """解析最大循环次数，支持按模块覆盖。"""

        default_rounds = int(self.agent_cfg.get("max_rounds", 2))
        overrides = self.agent_cfg.get("max_rounds_by_module", {})
        if isinstance(overrides, dict):
            if self.module_name in overrides:
                return int(overrides.get(self.module_name, default_rounds))
            if "default" in overrides:
                return int(overrides.get("default", default_rounds))
        return default_rounds
