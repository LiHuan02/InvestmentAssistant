import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class MCPManager:
    """管理外部 MCP 服务器，从 mcp_config.yaml 加载配置并解析环境变量。"""

    def __init__(self, config_path: str | None = None):
        self._servers: dict = {}
        if config_path:
            self._load_config(config_path)

    def _load_config(self, config_path: str) -> None:
        path = Path(config_path)
        if not path.exists():
            logger.info("MCP 配置文件不存在: %s", config_path)
            return
        try:
            with open(path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            raw = config.get("mcp_servers", {}) or {}
            for name, server_conf in raw.items():
                if not server_conf.get("enabled", True):
                    continue
                env = server_conf.get("env", {})
                resolved_env = {}
                for k, v in env.items():
                    if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                        var_name = v[2:-1]
                        resolved_env[k] = os.environ.get(var_name, "")
                    else:
                        resolved_env[k] = v
                server_conf["env"] = resolved_env
                self._servers[name] = server_conf
            logger.info("MCP 配置: %s", list(self._servers.keys()) or "无启用的服务器")
        except Exception as e:
            logger.warning("MCP 配置加载失败: %s", e)

    async def get_tools(self) -> list:
        """从所有已配置的 MCP 服务器获取工具。"""
        if not self._servers:
            return []
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            async with MultiServerMCPClient(self._servers) as client:
                tools = client.get_tools()
                logger.info("MCP 工具加载: %d 个 (来自 %s)", len(tools), list(self._servers.keys()))
                return tools
        except ImportError:
            logger.warning("langchain-mcp-adapters 未安装，MCP 不可用")
            return []
        except Exception as e:
            logger.warning("MCP 工具加载失败: %s", e)
            return []

    @property
    def server_names(self) -> list[str]:
        return list(self._servers.keys())
