import asyncio
import time
from typing import Any

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.core.logging import logger


class LoggingDashScopeEmbeddings(DashScopeEmbeddings):
    """带详细日志的 Embedding 包装类"""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        logger.debug(f"[Embed] 正在请求阿里云 API Embedding，批次大小: {len(texts)} 条文本...")
        start_time = time.time()
        try:
            result = super().embed_documents(texts)
            duration = time.time() - start_time
            logger.debug(f"[Embed] API 请求成功，耗时: {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"[Embed] API 请求失败! 耗时: {time.time() - start_time:.2f}s. 错误: {e}")
            raise e


class VectorStoreService:
    def __init__(self):
        self.persist_directory = str(settings.VECTOR_DB_PERSIST_DIR)
        self.collection_name = "policy_kb"
        self._client = None
        self._db = None
        self._embeddings = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = LoggingDashScopeEmbeddings(
                model="text-embedding-v3", dashscope_api_key=settings.DASHSCOPE_API_KEY
            )
        return self._embeddings

    def initialize(self):
        """延迟初始化，避免模块导入时锁定文件"""
        if self._client:
            return

        logger.info(f"Connecting to Qdrant (Local) at {self.persist_directory}...")
        self._client = QdrantClient(path=self.persist_directory)

        if not self._client.collection_exists(self.collection_name):
            logger.info(f"Collection '{self.collection_name}' not found. Creating...")
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )

        self._db = QdrantVectorStore(
            client=self._client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )

    @property
    def db(self) -> QdrantVectorStore:
        """获取数据库实例，如果未初始化则自动初始化"""
        if self._db is None:
            self.initialize()
        return self._db

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def add_documents(self, documents, user_id: str | None = None):
        """将文档列表添加到向量库"""
        if not documents:
            return
        logger.debug(f"[DB] 准备写入 {len(documents)} 个文档片段到 Qdrant...")

        # 如果 user_id 存在，注入到 metadata 中
        if user_id:
            for doc in documents:
                doc.metadata["user_id"] = user_id

        try:
            self.db.add_documents(documents=documents)
            logger.debug("[DB] 写入成功")
        except Exception as e:
            logger.error(f"[DB] 写入失败，准备重试。错误详情: {e}")
            raise e

    def search(self, query: str, k: int = 4, user_id: str | None = None):
        """同步语义检索"""
        logger.info(f"Searching for: {query}, user_id={user_id}")

        filter_condition = None
        if user_id:
            from qdrant_client.http import models as rest

            filter_condition = rest.Filter(
                must=[rest.FieldCondition(key="metadata.user_id", match=rest.MatchValue(value=user_id))]
            )

        return self.db.similarity_search(query, k=k, filter=filter_condition)

    def delete_by_metadata(self, key: str, value: str):
        """通过元数据过滤删除文档"""
        from qdrant_client.http import models as rest

        self.initialize()
        logger.info(f"[DB] Deleting vectors where {key} == {value}...")
        self._client.delete(
            collection_name=self.collection_name,
            points_selector=rest.FilterSelector(
                filter=rest.Filter(
                    must=[rest.FieldCondition(key=f"metadata.{key}", match=rest.MatchValue(value=value))]
                )
            ),
        )
        logger.info("[DB] Delete command sent.")

    async def asearch(self, query: str, k: int = 4, user_id: str | None = None) -> list[Any]:
        """异步语义检索 (在线程池中运行同步操作)"""
        logger.info(f"[Async] Searching for: {query}, user_id={user_id}")
        # 由于 Qdrant 本地客户端和 embed_query 都是同步阻塞的，必须放到线程池
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.search(query, k, user_id=user_id))


# 单例导出
vector_store = VectorStoreService()
