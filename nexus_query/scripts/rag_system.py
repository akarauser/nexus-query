import json
import os
from pathlib import Path
from uuid import uuid4

from langchain.agents import create_agent
from langchain.messages import AIMessageChunk, HumanMessage
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents.base import Document
from langchain_core.tools import tool
from langchain_docling.loader import DoclingLoader
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langfuse import get_client, observe, propagate_attributes
from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.memory import MemorySaver
from llm_guard.input_scanners import PromptInjection
from llm_guard.input_scanners.prompt_injection import MatchType
from numpy import ndarray
from sentence_transformers import CrossEncoder

from nexus_query.scripts.utils import logger

# Langfuse setup
langfuse = get_client()
handler = CallbackHandler()


class RagSystem:
    """Main class for RAG system"""

    # Attributes
    base_url = "http://ollama_nexus:11434"
    llm_model = ChatOllama(model=os.environ["MODEL_NAME"], base_url=base_url)
    embeddings_model = OllamaEmbeddings(
        model="nomic-embed-text:v1.5",
        base_url=base_url,
    )
    vector_store = Chroma(
        collection_name=os.environ["DB_NAME"],
        embedding_function=embeddings_model,
        persist_directory="nexus_query/data/" + os.environ["DB_NAME"],
    )
    if not os.path.exists(str(Path(__file__).parents[1] / "data/reranker")):
        pull_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
        pull_reranker.save_pretrained(str(Path(__file__).parents[1] / "data/reranker"))
        logger.debug("Reranker downloaded.")
    reranker = CrossEncoder(str(Path(__file__).parents[1] / "data/reranker"))
    logger.debug("Reranker loaded.")

    def __init__(self) -> None:
        self.agent = self._initialize_agent()
        self.thread_id = str(uuid4())

    def _create_documents_add_vector_store(self, pdf_path: str) -> None:
        """Create documents and add them to the vector store with uuid4

        Args:
            pdf_path: Path of PDF file
        """
        try:
            loader = DoclingLoader(file_path=pdf_path)
            documents = loader.load()
            documents = filter_complex_metadata(documents)
            uuids: list[str] = [str(uuid4()) for _ in range(len(documents))]
            self.vector_store.add_documents(documents=documents, ids=uuids)
            logger.debug("Documents added.")
        except Exception as e:
            logger.warning(f"Could not add documents: {e}")

    def _initialize_agent(self):
        """Initialize the agent with tools"""

        system_prompt = """You are an assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the question.
        Cite page numbers and reference documents while giving the answer and be thorough.
        If you don't know the answer state it. Do not try to create unrelated answers.

        # Available tool:
        - retrieve_context: Search the related documents

        # Output example:
            Answer:

            ----
            Sources(list):
                * Source 1 (Page number)
                * Source 2 (Page number)
                * Source 3 (Page number)
                * Source 4 (Page number)
        """

        agent = create_agent(
            model=self.llm_model,
            tools=[retrieve_context],
            system_prompt=system_prompt,
            checkpointer=MemorySaver(),
        )
        return agent

    async def _agent_stream(self, query: str):
        """Chat interaction as streaming output with agent

        Args:
            query: User input
        """
        with propagate_attributes(session_id=self.thread_id):
            async for chunk, metadata in self.agent.astream(
                {"messages": [HumanMessage(query)]},
                stream_mode="messages",
                config={"configurable": {"thread_id": self.thread_id}},
            ):
                if isinstance(chunk, AIMessageChunk):
                    data = {
                        "content": chunk.text,
                    }

                    yield (json.dumps(data) + "\n").encode()

    @observe(name="chat_stream")
    def chat(self, query: str):
        """Chat function with LLMGuard for prompt injection

        Args:
            query: User input
        """

        def fail_generator(sentence: str = "Sorry I cannot help you."):
            "Base answer for guarded prompts"
            words = sentence.split()
            for word in words:
                yield (json.dumps({"content": word + " "}) + "\n").encode()

        scanner = PromptInjection(threshold=0.5, match_type=MatchType.FULL)
        sanitized_prompt, is_valid, risk_score = scanner.scan(query)
        if risk_score > 0.5:
            return fail_generator()
        return self._agent_stream(query)


# Tools
@tool("retriever", description="Search, rerank and retrieve documents")
def retrieve_context(query: str) -> str:
    """Retrieve relevant information and rerank them by related to query from the documents for output"""
    documents: list[Document] = RagSystem.vector_store.similarity_search(query, k=4)
    pairs: list[list[str]] = [[query, doc.page_content] for doc in documents]
    if RagSystem.reranker is not None:
        scores: ndarray = RagSystem.reranker.predict(pairs)
        doc_score_pairs = list(zip(documents, scores))
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

        content = "\n\n".join(
            f"Source: {doc[0].metadata.get('source', '?')} (Page: {doc[0].metadata.get('page', '?')}): {doc[0].page_content}"
            for doc in doc_score_pairs
        )

        return content
    else:
        return "No content found."
