"""统一日志配置。

外部库：
- 日志库：提供标准日志能力。
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.utils.file_handler import read_yaml


def get_logger(name: str) -> logging.Logger:
    """
    获取统一格式的日志器。

    特性：
    - 同时输出到文件与控制台
    - 采用旋转日志避免文件无限增长
    - 配置统一来自 config/settings.yaml
    """

    settings = read_yaml("config/settings.yaml")
    logging_cfg = settings.get("logging", {})
    level_name = logging_cfg.get("level", "INFO")
    log_file = logging_cfg.get("file", "logs/app.log")

    logger = logging.getLogger(name)
    if logger.handlers:
        # 避免重复添加处理器（多次调用时常见问题）
        return logger

    logger.setLevel(getattr(logging, level_name.upper(), logging.INFO))

    # 确保日志目录存在
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # 文件日志：最大 1 兆，保留 3 个备份
    file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)

    # 控制台日志：便于本地调试
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
