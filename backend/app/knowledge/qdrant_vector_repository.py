from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.config import settings
from app.knowledge.vector_models import VectorPoint, VectorSearchResult
from app.knowledge.vector_repository import VectorRepository


class QdrantVectorRepository(VectorRepository):
    def __init__(self, url: str | None = None) -> None:
        self._url = url or settings.qdrant_url
        self._collection = settings.qdrant_collection
        self._client = AsyncQdrantClient(url=self._url)

    async def ensure_collection(self) -> None:
        collections = await self._client.get_collections()
        names = {c.name for c in collections.collections}
        if self._collection not in names:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=settings.vector_size, distance=Distance.COSINE),
            )

    async def upsert_points(self, points: list[VectorPoint]) -> None:
        if not points:
            return
        qdrant_points = [
            PointStruct(
                id=str(p.chunk_id),
                vector=p.vector,
                payload={
                    "chunk_id": str(p.chunk_id),
                    "document_id": str(p.document_id),
                    "page": p.page,
                    "section": p.section,
                    "chunk_index": p.chunk_index,
                },
            )
            for p in points
        ]
        await self._client.upsert(collection_name=self._collection, points=qdrant_points)

    async def search(self, vector: list[float], top_k: int) -> list[VectorSearchResult]:
        response = await self._client.query_points(
            collection_name=self._collection,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            VectorSearchResult(
                chunk_id=UUID(r.payload["chunk_id"]),
                document_id=UUID(r.payload["document_id"]),
                page=r.payload.get("page"),
                section=r.payload.get("section"),
                chunk_index=r.payload["chunk_index"],
                score=r.score,
            )
            for r in response.points
            if r.payload
        ]

    async def delete_by_document(self, document_id: UUID) -> None:
        await self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))]
            ),
        )

    async def delete_by_chunk_ids(self, chunk_ids: list[UUID]) -> None:
        if not chunk_ids:
            return
        await self._client.delete(
            collection_name=self._collection,
            points_selector=[str(cid) for cid in chunk_ids],
        )

    async def is_available(self) -> bool:
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False
