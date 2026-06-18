import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RAGService(ABC):
    """RAG 服务抽象接口。"""

    @abstractmethod
    def add_documents(self, documents: list[dict]) -> int:
        """添加文档到知识库，返回成功数量。"""
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """检索相关文档。"""
        ...

    def get_retriever(self) -> Any:
        """返回 LangChain 兼容的 Retriever。"""
        return None


class ChromaRAGService(RAGService):
    """基于 ChromaDB 的 RAG 实现。"""

    def __init__(self, persist_dir: str | None = None, collection_name: str = "investment_kb"):
        self._collection_name = collection_name
        self._persist_dir = persist_dir
        self._client = None
        self._collection = None
        try:
            import chromadb
            if persist_dir:
                Path(persist_dir).mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(path=persist_dir)
            else:
                self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB 初始化成功: %s (持久化: %s)", collection_name, persist_dir or "内存")
        except ImportError:
            logger.warning("chromadb 未安装，RAG 不可用")
        except Exception as e:
            logger.warning("ChromaDB 初始化失败: %s", e)

    @property
    def is_available(self) -> bool:
        return self._collection is not None

    def add_documents(self, documents: list[dict]) -> int:
        if not self._collection:
            return 0
        added = 0
        for doc in documents:
            try:
                doc_id = doc.get("id", str(hash(doc.get("content", ""))))
                self._collection.upsert(
                    ids=[doc_id],
                    documents=[doc.get("content", "")],
                    metadatas=[{k: v for k, v in doc.items() if k not in ("id", "content")}],
                )
                added += 1
            except Exception as e:
                logger.warning("添加文档失败: %s", e)
        logger.info("添加 %d/%d 个文档到知识库", added, len(documents))
        return added

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._collection:
            return []
        try:
            results = self._collection.query(query_texts=[query], n_results=top_k)
            docs = []
            for i in range(len(results.get("ids", [[]])[0])):
                doc = {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                }
                docs.append(doc)
            return docs
        except Exception as e:
            logger.warning("RAG 检索失败: %s", e)
            return []

    def get_retriever(self) -> Any:
        if not self._collection:
            return None
        try:
            from langchain_chroma import Chroma
            vectorstore = Chroma(
                client=self._client,
                collection_name=self._collection_name,
            )
            return vectorstore.as_retriever(search_kwargs={"k": 5})
        except ImportError:
            logger.warning("langchain-chroma 未安装")
            return None
