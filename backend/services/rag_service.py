import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class RAGService(ABC):
    """RAG 服务抽象接口，预留 ChromaDB 等向量数据库集成。"""

    @abstractmethod
    def add_documents(self, documents: list[dict]) -> int:
        """添加文档到知识库。返回成功添加的文档数。"""
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """检索与查询相关的文档。"""
        ...

    @abstractmethod
    def get_retriever(self):
        """返回 LangChain 兼容的 Retriever 对象。"""
        ...


class DummyRAGService(RAGService):
    """占位实现，未来替换为 ChromaDB 实现。"""

    def add_documents(self, documents: list[dict]) -> int:
        logger.info("DummyRAG: add_documents called with %d docs (no-op)", len(documents))
        return 0

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        logger.info("DummyRAG: search called for '%s' (no-op)", query[:50])
        return []

    def get_retriever(self):
        return None
