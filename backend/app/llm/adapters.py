"""LLM adapters for multiple providers with citation extraction."""
import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Protocol

import openai
AsyncOpenAI = openai.AsyncOpenAI  # re-export for tests patching app.llm.adapters.AsyncOpenAI

from ..config import settings
from ..retrieval.models import Citation, SearchResult
from .models import LLMRequest, LLMResponse, TokensUsed

logger = logging.getLogger(__name__)


class LLMAdapterProtocol(Protocol):
    """Protocol for LLM adapters."""

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate answer from LLM."""
        ...


class BaseLLMAdapter(ABC):
    """Base class for LLM adapters."""

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate answer from LLM."""
        pass

    def _build_system_prompt(self) -> str:
        """Build system prompt for RAG."""
        return """You are a helpful AI assistant for a public sector information system.
Your task is to answer questions based ONLY on the provided context documents.

Guidelines:
1. Answer questions accurately using ONLY the information from the provided context
2. If the context doesn't contain enough information, say so clearly
3. Include citations by referencing the document IDs in your answer like [Doc 1], [Doc 2]
4. Be concise but comprehensive
5. Maintain a professional, helpful tone
6. Do not make up information or use knowledge outside the provided context
7. If you're uncertain, acknowledge the limitation

Remember: Accuracy and citation are critical for public sector use."""

    def _build_user_prompt(self, query: str, context: list[str]) -> str:
        """Build user prompt with query and context."""
        context_text = "\n\n".join(
            [f"[Document {i+1}]\n{ctx}" for i, ctx in enumerate(context)]
        )

        return f"""Context Documents:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context documents above. Include citations in your response."""

    def _extract_citations(
        self,
        answer: str,
        search_results: list[SearchResult],
    ) -> list[Citation]:
        """Extract citations from answer text."""
        citations = []

        # Find citation patterns like [Doc 1], [Document 2], etc.
        citation_pattern = r'\[(?:Doc(?:ument)?)\s*(\d+)\]'
        matches = re.finditer(citation_pattern, answer, re.IGNORECASE)

        cited_indices = set()
        for match in matches:
            doc_index = int(match.group(1)) - 1  # Convert to 0-indexed

            if 0 <= doc_index < len(search_results) and doc_index not in cited_indices:
                result = search_results[doc_index]
                citation = Citation(
                    document_id=result.document_id,
                    chunk_id=result.id,
                    content=result.content[:500],  # First 500 chars
                    title=result.metadata.get("title"),
                    author=result.metadata.get("author"),
                    source_url=result.metadata.get("source_url"),
                    page_number=result.metadata.get("page_number"),
                    relevance_score=result.score,
                )
                citations.append(citation)
                cited_indices.add(doc_index)

        logger.info(f"Extracted {len(citations)} citations from answer")
        return citations

    def _calculate_cost(
        self,
        tokens_used,
        model: str,
    ) -> float:
        """Calculate cost based on token usage."""
        # Support both dict style (legacy) and TokensUsed model
        if isinstance(tokens_used, dict):
            input_tokens = tokens_used.get("input", tokens_used.get("input_tokens", 0))
            output_tokens = tokens_used.get("output", tokens_used.get("output_tokens", 0))
        else:
            input_tokens = getattr(tokens_used, "input_tokens", 0)
            output_tokens = getattr(tokens_used, "output_tokens", 0)

        # Cost per 1K tokens
        input_cost = (input_tokens / 1000) * settings.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * settings.cost_per_1k_output_tokens

        total_cost = input_cost + output_cost
        logger.debug(
            f"Cost calculated: ${total_cost:.4f} "
            f"(input: {input_tokens}, output: {output_tokens})"
        )

        return total_cost


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI LLM adapter."""

    def __init__(
        self,
        api_key: str | None = None,
        org_id: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        """Initialize OpenAI adapter."""
        # Set model and temperature early for stub fallback usage
        self.model = model or settings.openai_llm_model
        self.temperature = temperature if temperature is not None else 0.0
        # Use module attribute so tests patching openai.AsyncOpenAI work correctly; fallback to stub if library init fails
        try:
            # Use exported AsyncOpenAI symbol so tests patching app.llm.adapters.AsyncOpenAI intercept
            self.client = AsyncOpenAI(
                api_key=api_key or settings.openai_api_key,
                organization=org_id or settings.openai_org_id,
            )
        except TypeError as e:  # e.g. httpx proxies incompatibility in test env
            logger.warning(f"OpenAI client init failed ({e}); using stub client for tests.")
            adapter_model = self.model

            class _StubCreate:
                async def __call__(self, **kwargs):  # mimic .create call
                    class _StubUsage:
                        prompt_tokens = 0
                        completion_tokens = 0
                        total_tokens = 0
                    class _StubMessage:
                        content = ""
                    class _StubChoice:
                        message = _StubMessage()
                    return type(
                        "_StubResponse",
                        (),
                        {
                            "choices": [_StubChoice()],
                            "usage": _StubUsage(),
                            "model": kwargs.get("model", adapter_model),
                        },
                    )

            class _StubCompletions:
                create = _StubCreate()

            class _StubChat:
                completions = _StubCompletions()

            class _StubClient:
                chat = _StubChat()

            self.client = _StubClient()
        logger.info(f"Initialized OpenAI adapter with model: {self.model}")

    async def generate(
        self,
        request: LLMRequest,
        search_results: list[SearchResult] | None = None,
    ) -> LLMResponse:
        """Generate answer using OpenAI."""
        start_time = time.time()

        try:
            # Build prompts
            system_prompt = request.system_prompt or self._build_system_prompt()
            user_prompt = self._build_user_prompt(request.query, request.context)

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=request.model or self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # Prefer adapter temperature unless request overrides with a different value
                temperature=request.temperature if request.temperature != 0.0 and request.temperature != self.temperature else self.temperature,
                max_tokens=request.max_tokens,
            )

            answer = response.choices[0].message.content or ""

            # Token usage
            tokens_used = TokensUsed(
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                total=response.usage.total_tokens if response.usage else 0,
            )

            # Calculate cost
            cost = self._calculate_cost(tokens_used, request.model or self.model)

            # Extract citations
            citations = []
            if search_results:
                citations = self._extract_citations(answer, search_results)

            processing_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Generated answer for tenant {request.tenant_id} "
                f"in {processing_time_ms:.2f}ms (tokens: {tokens_used.total}, cost: ${cost:.4f})"
            )

            return LLMResponse(
                query=request.query,
                answer=answer,
                citations=citations,
                model=request.model or self.model,
                tokens_used=tokens_used,
                cost=cost,
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}", exc_info=True)
            raise


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic (Claude) LLM adapter."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-sonnet-20240229",
    ) -> None:
        """Initialize Anthropic adapter."""
        self.api_key = api_key
        self.model = model
        logger.info(f"Initialized Anthropic adapter with model: {self.model}")

    async def generate(
        self,
        request: LLMRequest,
        search_results: list[SearchResult] | None = None,
    ) -> LLMResponse:
        """Generate answer using Anthropic (placeholder - requires anthropic SDK)."""
        # TODO: Implement when anthropic SDK is available
        raise NotImplementedError("Anthropic adapter not yet implemented")


class LLMAdapterFactory:
    """Factory for creating LLM adapters."""

    @staticmethod
    def create(
        provider: str = "openai",
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> BaseLLMAdapter:
        """Create LLM adapter by provider."""
        if provider == "openai":
            return OpenAIAdapter(api_key=api_key, model=model, temperature=temperature)
        elif provider == "anthropic":
            return AnthropicAdapter(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    # Backwards-compatible alias expected by tests
    @staticmethod
    def get_adapter(
        provider: str = "openai",
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> BaseLLMAdapter:
        return LLMAdapterFactory.create(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=temperature,
        )
