"""
Proveedores asíncronos de LLM para EvolutIA.
Usa asyncio para llamadas concurrentes a APIs de LLM.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional
from functools import wraps

from .retry_utils import retry_async

logger = logging.getLogger(__name__)


def async_sync_wrapper(sync_func):
    """
    Wrapper para ejecutar funciones síncronas de forma asíncrona usando run_in_executor.

    Args:
        sync_func: Función síncrona a envolver

    Returns:
        Función asíncrona que ejecuta la función síncrona en un executor
    """
    @wraps(sync_func)
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_func, *args, **kwargs)
    return async_wrapper


class AsyncLLMProvider(ABC):
    """Clase base abstracta para proveedores asíncronos de LLM."""

    DEFAULT_SYSTEM_PROMPT = "Eres un experto en métodos matemáticos para física e ingeniería."
    DEFAULT_MAX_TOKENS = 2000
    DEFAULT_TEMPERATURE = 0.7

    def __init__(self, model_name: Optional[str] = None):
        """
        Inicializa el proveedor asíncrono de LLM.

        Args:
            model_name: Nombre del modelo a usar
        """
        self.model_name = model_name

    @abstractmethod
    async def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """Genera contenido de forma asíncrona."""
        pass


class AsyncOpenAIProvider(AsyncLLMProvider):
    """Proveedor asíncrono para OpenAI."""

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name)
        self.sync_provider = None

        try:
            from evolutia.llm_providers import OpenAIProvider
            self.sync_provider = OpenAIProvider(model_name=model_name)
            logger.debug("[AsyncOpenAIProvider] Inicializado con proveedor síncrono")
        except Exception as e:
            logger.error(f"[AsyncOpenAIProvider] Error inicializando proveedor síncrono: {e}")

    @retry_async(max_retries=3, initial_delay=1.0, max_delay=10.0)
    async def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """Genera contenido usando el proveedor síncrono en un executor."""
        if not self.sync_provider:
            return None

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.sync_provider.generate_content,
            prompt,
            system_prompt,
            kwargs
        )
        return result


class AsyncAnthropicProvider(AsyncLLMProvider):
    """Proveedor asíncrono para Anthropic."""

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name)
        self.sync_provider = None

        try:
            from evolutia.llm_providers import AnthropicProvider
            self.sync_provider = AnthropicProvider(model_name=model_name)
            logger.debug("[AsyncAnthropicProvider] Inicializado con proveedor síncrono")
        except Exception as e:
            logger.error(f"[AsyncAnthropicProvider] Error inicializando proveedor síncrono: {e}")

    @retry_async(max_retries=3, initial_delay=1.0, max_delay=10.0)
    async def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """Genera contenido usando el proveedor síncrono en un executor."""
        if not self.sync_provider:
            return None

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.sync_provider.generate_content,
            prompt,
            system_prompt,
            kwargs
        )
        return result


class AsyncGeminiProvider(AsyncLLMProvider):
    """Proveedor asíncrono para Gemini."""

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name)
        self.sync_provider = None

        try:
            from evolutia.llm_providers import GeminiProvider
            self.sync_provider = GeminiProvider(model_name=model_name)
            logger.debug("[AsyncGeminiProvider] Inicializado con proveedor síncrono")
        except Exception as e:
            logger.error(f"[AsyncGeminiProvider] Error inicializando proveedor síncrono: {e}")

    @retry_async(max_retries=3, initial_delay=1.0, max_delay=10.0)
    async def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """Genera contenido usando el proveedor síncrono en un executor."""
        if not self.sync_provider:
            return None

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.sync_provider.generate_content,
            prompt,
            system_prompt,
            kwargs
        )
        return result


def get_async_provider(provider_name: str, **kwargs) -> AsyncLLMProvider:
    """Factory method para obtener un proveedor asíncrono."""
    if provider_name == "openai":
        return AsyncOpenAIProvider(**kwargs)
    elif provider_name == "anthropic":
        return AsyncAnthropicProvider(**kwargs)
    elif provider_name == "gemini":
        return AsyncGeminiProvider(**kwargs)
    else:
        raise ValueError(f"Proveedor asíncrono desconocido: {provider_name}")
