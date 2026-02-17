"""认证初始化：获取并持久化接口 token。

外部库：
- requests: 发送登录请求获取 token。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import requests

from src.utils.file_handler import read_text, read_yaml, write_yaml
from src.utils.logger import get_logger


class AuthSetup:
    """
    认证初始化：通过登录接口获取 Token，并回写到配置与文档中。

    功能点：
    - 读取 auth 配置（登录地址、账号密码、token 路径）
    - 发起登录请求并解析 token
    - 更新 settings.yaml 中的 token
    - 将 raw_docs 中的 `{your_token_here}` 替换为实际 token
    """

    def __init__(self, settings_path: str = "config/settings.yaml") -> None:
        self._logger = get_logger(__name__)
        self.settings_path = settings_path
        self.settings = read_yaml(settings_path)

    def run(self) -> str:
        """执行登录获取 token 并落盘。"""

        auth_cfg = self.settings.get("auth", {})
        login_url = auth_cfg.get("login_url")
        username = auth_cfg.get("username")
        password = auth_cfg.get("password")
        headers = auth_cfg.get("headers", {})
        token_path = auth_cfg.get("token_json_path", "data.token")
        token_prefix = auth_cfg.get("token_prefix", "Bearer ")

        if not login_url or not username or not password:
            raise ValueError("Auth config missing login_url/username/password.")

        payload = {"username": username, "password": password}
        self._logger.info("Requesting token from %s", login_url)

        response = requests.post(login_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        token = self._extract_token(response.json(), token_path)
        if not token:
            raise ValueError("Token not found in login response.")

        # 写回配置
        self.settings.setdefault("auth", {})["token"] = token
        write_yaml(self.settings_path, self.settings)
        self._logger.info("Token saved to settings.yaml")

        # 将 token 写入 raw_docs 中的占位符
        raw_docs_dir = Path(self.settings.get("paths", {}).get("raw_docs_dir", "data/raw_docs"))
        self._replace_token_in_docs(raw_docs_dir, f"{token_prefix}{token}")

        return token

    def _extract_token(self, data: Dict[str, Any], path: str) -> str:
        """根据简单的 dot path 提取 token，例如 data.token。"""

        current: Any = data
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return ""
            current = current[key]
        return str(current)

    def _replace_token_in_docs(self, raw_docs_dir: Path, token_value: str) -> None:
        """将 raw_docs 内所有文档中的占位符替换为实际 token。"""

        if not raw_docs_dir.exists():
            self._logger.warning("Raw docs directory not found: %s", raw_docs_dir)
            return

        for path in raw_docs_dir.iterdir():
            if path.suffix not in {".md", ".txt"}:
                continue
            content = read_text(str(path))
            if "{your_token_here}" not in content:
                continue
            updated = content.replace("{your_token_here}", token_value)
            path.write_text(updated, encoding="utf-8")
            self._logger.info("Token replaced in doc: %s", path)
