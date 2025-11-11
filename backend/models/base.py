from typing import Protocol, List, Dict, Any, Optional

class InsightLLM(Protocol):
    """Minimal interface any LLM provider must implement for this use-case."""

    def generate(
        self,
        prompt: str,
        images: List[bytes],
        *,
        temperature: float = 0.6,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return markdown text for (prompt + images). Should raise provider-specific errors on failure."""
        ...