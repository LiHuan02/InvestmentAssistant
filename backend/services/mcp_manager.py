import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class MCPManager:
    """MCP 服务器管理器，负责加载配置和管理 MCP 服务器生命周期。"""

    def __init__(self, config_path: str | None = None):
        self._servers: dict = {}
        self._tools: list = []
        if config_path:
            self._load_config(config_path)

    def _load_config(self, config_path: str) -> None:
        path = Path(config_path)
        if not path.exists():
            logger.info("MCP 配置文件不存在: %s", config_path)
            return
        try:
            with open(path) as f:
                config = yaml.safe_load(f) or {}
            self._servers = config.get("mcp_servers", {})
            logger.info("加载 MCP 配置: %d 个服务器", len(self._servers))
        except Exception as e:
            logger.warning("加载 MCP 配置失败: %s", e)

    async def get_tools(self) -> list:
        """从所有已配置的 MCP 服务器获取工具列表。"""
        if not self._servers:
            return []

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            async with MultiServerMCPClient(self._servers) as client:
                self._tools = client.get_tools()
                logger.info("从 MCP 服务器加载 %d 个工具", len(self._tools))
                return self._tools
        except ImportError:
            logger.warning("langchain-mcp-adapters 未安装，MCP 不可用")
            return []
        except Exception as e:
            logger.warning("MCP 工具加载失败: %s", e)
            return []

    @property
    def server_names(self) -> list[str]:
        return list(self._servers.keys())
