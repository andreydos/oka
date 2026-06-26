from uuid import UUID

from app.chat.citation_service import CitationService
from app.chat.language_utils import get_messages
from app.chat.prompt_builder import NOT_FOUND_MESSAGE, build_system_prompt, build_user_prompt, is_list_question
from app.chat.query_classifier import is_greeting, is_too_vague
from app.chat.retrieval_filter import filter_search_results
from app.chat.retrieval_query import build_retrieval_query, build_search_queries, merge_search_results
from app.config import settings
from app.db.models import MessageRole
from app.documents.document_repository import ChatRepository, DocumentRepository
from app.knowledge.embedding_service import EmbeddingService
from app.knowledge.vector_repository import VectorRepository
from app.llm.llm_client import LLMClient
from app.ml_mutex import MLMutex


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        document_repository: DocumentRepository,
        vector_repository: VectorRepository,
        embedding_service: EmbeddingService,
        llm_client: LLMClient,
        citation_service: CitationService | None = None,
    ) -> None:
        self._chat_repository = chat_repository
        self._document_repository = document_repository
        self._vector_repository = vector_repository
        self._embedding_service = embedding_service
        self._llm_client = llm_client
        self._citation_service = citation_service or CitationService()

    async def create_session(self, title: str = "New chat"):
        return await self._chat_repository.create_session(title)

    async def list_sessions(self):
        return await self._chat_repository.list_sessions()

    async def get_session(self, session_id: UUID):
        return await self._chat_repository.get_session_with_messages(session_id)

    async def get_documents_for_citations(self, session) -> dict:
        doc_ids: set[UUID] = set()
        for msg in session.messages:
            for c in msg.citations:
                doc_ids.add(c.document_id)
        return await self._chat_repository.get_documents_by_ids(list(doc_ids))

    async def send_message(self, session_id: UUID, content: str) -> dict:
        session = await self._chat_repository.get_session_with_messages(session_id)
        if not session:
            raise ValueError("Session not found")

        if session.title == "New chat":
            await self._chat_repository.update_session_title(session_id, content[:80])

        user_message = await self._chat_repository.add_message(
            session_id, MessageRole.USER, content
        )

        messages = get_messages()

        if is_greeting(content) or is_too_vague(content):
            assistant_message = await self._chat_repository.add_message(
                session_id, MessageRole.ASSISTANT, messages["off_topic"]
            )
            return {"user_message": user_message, "assistant_message": assistant_message, "citations": []}

        if not await self._llm_client.is_available():
            raise RuntimeError("LLM service unavailable")

        prior_user_messages = [m.content for m in session.messages if m.role == MessageRole.USER]
        retrieval_query = build_retrieval_query(content, prior_user_messages)
        list_question = is_list_question(content) or is_list_question(retrieval_query)

        search_queries = build_search_queries(retrieval_query)

        search_limit = max(settings.top_k * 2, 10)
        result_sets: list = []
        for search_text in search_queries:
            query_vector = await self._embedding_service.embed_query(search_text)
            result_sets.append(await self._vector_repository.search(query_vector, search_limit))
        search_results = merge_search_results(*result_sets, limit=search_limit)

        all_chunk_ids = [r.chunk_id for r in search_results]
        all_chunks = await self._document_repository.get_chunks_by_ids(all_chunk_ids)
        relevant = filter_search_results(search_results, all_chunks, retrieval_query)

        if not relevant:
            assistant_message = await self._chat_repository.add_message(
                session_id, MessageRole.ASSISTANT, messages["not_found"]
            )
            return {"user_message": user_message, "assistant_message": assistant_message, "citations": []}

        chunk_map = {c.id: c for c in all_chunks}
        chunks = [chunk_map[r.chunk_id] for r in relevant if r.chunk_id in chunk_map]
        doc_ids = list({c.document_id for c in chunks})
        documents = await self._chat_repository.get_documents_by_ids(doc_ids)

        contexts = []
        for result in relevant:
            chunk = chunk_map.get(result.chunk_id)
            if not chunk:
                continue
            doc = documents.get(chunk.document_id)
            contexts.append(
                {
                    "document_name": doc.filename if doc else "Unknown",
                    "page": chunk.page,
                    "section": chunk.section,
                    "text": chunk.text,
                }
            )

        citation_records = self._citation_service.build_citation_records(
            relevant,
            all_chunks,
            retrieval_query,
        )
        not_found_message = messages["not_found"]
        system_prompt = build_system_prompt(not_found_message, list_question=list_question)
        user_prompt = build_user_prompt(content, contexts, list_question=list_question)

        async with MLMutex():
            answer = await self._llm_client.generate(user_prompt, system_prompt)

        if not_found_message in answer or NOT_FOUND_MESSAGE in answer:
            answer = not_found_message
            citation_records = []

        assistant_message = await self._chat_repository.add_message(
            session_id,
            MessageRole.ASSISTANT,
            answer,
            citations=citation_records if citation_records else None,
        )

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "citations": citation_records,
            "documents": documents,
        }
