import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage,
    Document as LlamaDocument,
)
from llama_index.core.indices.base import IndexType, BaseIndex
from llama_index.llms.dashscope import DashScope
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.callbacks import CallbackManager

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LlamaIndexService:
    def __init__(self):
        self.index: Optional[BaseIndex] = None
        self.documents: List[LlamaDocument] = []
        self.llm: Optional[DashScope] = None
        self.embed_model: Optional[DashScopeEmbedding] = None

    async def setup(self):
        """Initialize LlamaIndex with LLM and Embedding settings"""
        logger.info("[LlamaIndex] Initializing...")
        self.llm = DashScope(
            model=settings.LLM_MODEL,
            api_key=settings.DASHSCOPE_API_KEY,
            temperature=settings.TEMPERATURE,
            top_p=settings.TOP_P,
        )
        self.embed_model = DashScopeEmbedding(
            model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V1,
            api_key=settings.DASHSCOPE_API_KEY,
        )

        Settings.llm = self.llm
        Settings.embed_model = self.embed_model

        # Configure chunking
        Settings.node_parser = SentenceSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        logger.info("[LlamaIndex] Initialized successfully")
        return self.llm, self.embed_model

    async def load_documents(self, directory: str) -> List[LlamaDocument]:
        """Load documents from a directory"""
        logger.info("[LlamaIndex] Loading documents from %s", directory)

        if not os.path.exists(directory):
            logger.info("[LlamaIndex] Directory %s does not exist", directory)
            return []

        try:
            reader = SimpleDirectoryReader(directory)
            documents = await asyncio.to_thread(reader.load_data)
            self.documents = documents
            logger.info("[LlamaIndex] Loaded %s documents", len(documents))
            return documents
        except Exception as e:
            logger.exception("[LlamaIndex] Error loading documents: %s", e)
            return []

    async def build_index(self, documents: Optional[List[LlamaDocument]] = None) -> BaseIndex:
        """Build or load vector index from documents"""
        docs_to_index = documents or self.documents

        # Try to load existing index
        if os.path.exists(settings.STORAGE_DIR):
            try:
                storage_context = StorageContext.from_defaults(persist_dir=settings.STORAGE_DIR)
                self.index = await asyncio.to_thread(load_index_from_storage, storage_context)
                logger.info("[LlamaIndex] Loaded existing index from %s", settings.STORAGE_DIR)
                return self.index
            except Exception as e:
                logger.warning("[LlamaIndex] Could not load existing index: %s", e)

        if not docs_to_index:
            logger.info("[LlamaIndex] No documents to index")
            return None

        # Build new index
        logger.info("[LlamaIndex] Building index from %s documents...", len(docs_to_index))
        self.index = await asyncio.to_thread(VectorStoreIndex.from_documents, docs_to_index)

        # Persist index
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        self.index.storage_context.persist(persist_dir=settings.STORAGE_DIR)
        logger.info("[LlamaIndex] Index built and persisted to %s", settings.STORAGE_DIR)

        return self.index

    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        callback_handler: Any = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using similarity search"""
        if not self.index:
            logger.warning("[LlamaIndex] No index available for querying")
            return []

        try:
            if callback_handler is not None:
                Settings.callback_manager = CallbackManager([callback_handler])

            retriever_kwargs: Dict[str, Any] = {"similarity_top_k": top_k}
            if tenant_id:
                retriever_kwargs["filters"] = MetadataFilters(
                    filters=[ExactMatchFilter(key="tenant_id", value=tenant_id)]
                )

            retriever = self.index.as_retriever(**retriever_kwargs)
            nodes = await asyncio.to_thread(retriever.retrieve, query_text)

            results = []
            for node in nodes:
                results.append({
                    "content": node.text,
                    "score": round(node.score, 4) if node.score else None,
                    "metadata": {
                        "file_name": node.metadata.get("file_name", "Unknown"),
                        "page_label": node.metadata.get("page_label"),
                    }
                })

            logger.info("[LlamaIndex] Retrieved %s documents for query", len(results))
            return results

        except Exception as e:
            logger.exception("[LlamaIndex] Error during query: %s", e)
            return []

    async def add_document(self, file_path: str, file_name: str) -> bool:
        """Add a new document to the index"""
        try:
            # Load the document
            reader = SimpleDirectoryReader(input_files=[file_path])
            documents = await asyncio.to_thread(reader.load_data)

            if not documents:
                print(f"[LlamaIndex] Could not load document from {file_path}")
                return False

            # Add metadata to documents
            for doc in documents:
                doc.metadata["file_name"] = file_name
                doc.metadata["uploaded_at"] = datetime.now().isoformat()
                doc.metadata.setdefault("tenant_id", settings.DEFAULT_TENANT_ID)

            # Insert into index
            if self.index:
                for doc in documents:
                    await asyncio.to_thread(self.index.insert, doc)

                # Persist updated index
                self.index.storage_context.persist(persist_dir=settings.STORAGE_DIR)
                logger.info("[LlamaIndex] Document %s added to index", file_name)
                return True
            else:
                logger.warning("[LlamaIndex] No index available to add document")
                return False

        except Exception as e:
            logger.exception("[LlamaIndex] Error adding document: %s", e)
            return False

    def get_index_status(self) -> Dict[str, Any]:
        """Get current index status"""
        return {
            "indexed": self.index is not None,
            "document_count": len(self.documents) if self.documents else 0,
            "last_updated": datetime.now().isoformat() if self.index else None,
            "storage_path": settings.STORAGE_DIR,
        }

    async def clear_index(self) -> bool:
        """Clear the current index and storage"""
        try:
            self.index = None
            self.documents = []

            # Remove storage directory
            if os.path.exists(settings.STORAGE_DIR):
                import shutil
                shutil.rmtree(settings.STORAGE_DIR)
                logger.info("[LlamaIndex] Cleared index and storage at %s", settings.STORAGE_DIR)

            return True

        except Exception as e:
            logger.exception("[LlamaIndex] Error clearing index: %s", e)
            return False


# Global service instance
llamaindex_service = LlamaIndexService()
