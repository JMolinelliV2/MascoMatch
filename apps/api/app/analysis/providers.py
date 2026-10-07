from abc import ABC, abstractmethod
import base64

import httpx2 as httpx

from app.analysis.prompts import TEXT_PROMPT, VISION_PROMPT
from app.analysis.schemas import AnimalFeatures, ExtractionOutput, parse_extraction_output
from app.core.config import settings


class ProviderError(Exception):
    def __init__(self, code: str, retryable: bool = True):
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class LLMProvider(ABC):
    @abstractmethod
    async def extract_observation(self, text: str) -> AnimalFeatures:
        """Extract attributes from text without changing the original evidence."""


class VisionProvider(ABC):
    @abstractmethod
    async def analyze_image(self, image: bytes, mime_type: str) -> AnimalFeatures:
        """Extract observable attributes; image embeddings belong to phase 3."""


class ExtractionProvider(LLMProvider, VisionProvider):
    """Replaceable contract for semantic extraction, separate from embeddings."""


class OllamaProvider(ExtractionProvider):
    def __init__(self, model: str, base_url: str | None = None):
        self.model = model
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def _extract(self, prompt: str, message: dict, source: str) -> AnimalFeatures:
        try:
            async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds, follow_redirects=False, trust_env=False) as client:
                details = await client.post(f"{self.base_url}/api/show", json={"model": self.model})
                if details.status_code == 404:
                    raise ProviderError("MODEL_UNAVAILABLE", retryable=False)
                if details.status_code in (401, 403):
                    raise ProviderError("PROVIDER_AUTH_FAILED", retryable=False)
                details.raise_for_status()
                capabilities = details.json().get("capabilities", [])
                if "vision" not in capabilities and capabilities and source == "image":
                    raise ProviderError("MODEL_HAS_NO_VISION", retryable=False)
                body = {
                    "model": self.model,
                    "messages": [{"role": "system", "content": prompt}, {"role": "user", **message}],
                    "format": ExtractionOutput.model_json_schema(),
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": 4096, "num_ctx": 8192},
                }
                if "thinking" in capabilities:
                    body["think"] = False
                response = await client.post(f"{self.base_url}/api/chat", json=body)
                if response.status_code == 404:
                    raise ProviderError("MODEL_UNAVAILABLE", retryable=False)
                if response.status_code in (401, 403):
                    raise ProviderError("PROVIDER_AUTH_FAILED", retryable=False)
                if response.status_code in (400, 422):
                    raise ProviderError("PROVIDER_CONFIGURATION_ERROR", retryable=False)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ProviderError("INVALID_FEATURE_RESPONSE")
                if data.get("done") is not True or data.get("done_reason") == "length":
                    raise ProviderError("INCOMPLETE_MODEL_RESPONSE")
                return parse_extraction_output(data["message"]["content"], source)
        except ProviderError:
            raise
        except httpx.TimeoutException as exc:
            raise ProviderError("PROVIDER_TIMEOUT") from exc
        except httpx.HTTPError as exc:
            raise ProviderError("PROVIDER_UNAVAILABLE") from exc
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ProviderError("INVALID_FEATURE_RESPONSE") from exc

    async def extract_observation(self, text: str) -> AnimalFeatures:
        return await self._extract(TEXT_PROMPT, {"content": "Animal evidence:\n" + text}, "text")

    async def analyze_image(self, image: bytes, mime_type: str) -> AnimalFeatures:
        return await self._extract(VISION_PROMPT, {
            "content": "Extract the visible animal's physical characteristics as JSON.",
            "images": [base64.b64encode(image).decode("ascii")],
        }, "image")


def get_provider(provider: str, model: str) -> ExtractionProvider:
    if provider == "ollama":
        return OllamaProvider(model)
    raise ProviderError("PROVIDER_NOT_CONFIGURED", retryable=False)
