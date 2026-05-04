"""
Módulo que define los proveedores de LLM abstractos y concretos.
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from evolutia.cache.llm_cache import LLMCache

class LLMProvider(ABC):
    """Clase base abstracta para proveedores de LLM."""

    DEFAULT_SYSTEM_PROMPT = "Eres un experto en métodos matemáticos para física e ingeniería."
    DEFAULT_MAX_TOKENS = 2000
    DEFAULT_TEMPERATURE = 0.7

    def __init__(self, model_name: Optional[str] = None, cache: Optional['LLMCache'] = None):
        """
        Inicializa el proveedor de LLM.

        Args:
            model_name: Nombre del modelo a usar
            cache: Instancia opcional de LLMCache para cachear respuestas
        """
        self.model_name = model_name
        self.client = None
        self.genai = None
        self.cache = cache
        self.api_key = self._get_api_key()
        if self.api_key:
            self._setup_client()

        if self.cache:
            logger.debug("[LLMProvider] Caché de LLM habilitado")

    @abstractmethod
    def _get_api_key(self) -> Optional[str]:
        """Obtiene la API key de las variables de entorno."""
        pass

    @abstractmethod
    def _setup_client(self):
        """Configura el cliente de la API."""
        pass

    @abstractmethod
    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """Genera contenido a partir de un prompt."""
        pass

    def _get_provider_name(self) -> str:
        """
        Obtiene el nombre del proveedor para usar en el caché.

        Returns:
            Nombre del proveedor (ej: 'OpenAI', 'Anthropic')
        """
        return self.__class__.__name__.replace('Provider', '')


class OpenAICompatibleProvider(LLMProvider):
    """Base clase para proveedores compatibles con OpenAI API."""

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None, timeout: Optional[float] = None, cache: Optional['LLMCache'] = None):
        """
        Inicializa el proveedor OpenAI-compatible.

        Args:
            model_name: Nombre del modelo a usar
            base_url: URL base de la API (para proveedores compatibles)
            timeout: Timeout para las llamadas a la API
            cache: Instancia opcional de LLMCache
        """
        self.base_url = base_url
        self.timeout = timeout
        super().__init__(model_name, cache=cache)

    def _setup_openai_client(self, api_key: Optional[str], base_url: Optional[str] = None, timeout: Optional[float] = None) -> bool:
        """
        Configura cliente OpenAI compartido.

        Returns:
            True si la configuración fue exitosa
            False si no se pudo configurar (cliente no inicializado)
        """
        if not api_key:
            return False
        try:
            from openai import OpenAI
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            if timeout is not None:
                client_kwargs["timeout"] = timeout
            self.client = OpenAI(**client_kwargs)
            logger.info(f"[OpenAICompatibleProvider] Cliente OpenAI inicializado (base_url={base_url}, timeout={timeout})")
            return True
        except ImportError:
            logger.error("[OpenAICompatibleProvider] Biblioteca openai no instalada. Instala con: pip install openai")
            self.client = None
            return False
        except Exception as e:
            logger.error(f"[OpenAICompatibleProvider] Error inesperado inicializando cliente OpenAI: {e}")
            self.client = None
            return False

    def _openai_generate_content(self, provider_name: str, default_model: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Genera contenido usando API OpenAI-compatible con caché.

        Returns:
            Contenido generado si la llamada fue exitosa
            None si hubo un error de API o configuración
        """
        if not self.client:
            logger.error(f"[{provider_name}] Cliente no inicializado, no se puede generar contenido")
            return None

        system_content = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        model = self.model_name or default_model
        prompt = kwargs.get("prompt", "")

        # Intentar caché primero
        if self.cache:
            cached = self.cache.get(prompt, self._get_provider_name(), model)
            if cached:
                logger.info(f"[{provider_name}] Contenido obtenido del caché (modelo={model})")
                return cached

        # Generar respuesta
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", self.DEFAULT_TEMPERATURE),
                max_tokens=kwargs.get("max_tokens", self.DEFAULT_MAX_TOKENS)
            )
            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            
            if hasattr(message, 'content') and message.content is not None:
                content = message.content.strip()
            else:
                content = ""
                logger.warning(f"[{provider_name}] Message content is None")

            if not content:
                logger.warning(f"[{provider_name}] Contenido vacío recibido. Finish reason: {finish_reason}")
                logger.debug(f"[{provider_name}] Raw response: {response}")

            logger.info(f"[{provider_name}] Contenido generado exitosamente (modelo={model}, longitud={len(content)}, reason={finish_reason})")

            # Guardar en caché
            if self.cache:
                metadata = {
                    'provider': provider_name,
                    'model': model,
                    'temperature': kwargs.get("temperature", self.DEFAULT_TEMPERATURE),
                    'max_tokens': kwargs.get("max_tokens", self.DEFAULT_MAX_TOKENS)
                }
                self.cache.put(prompt, provider_name, model, content, metadata=metadata)

            return content
        except Exception as e:
            logger.error(f"[{provider_name}] Error en llamada a API: {e}")
            return None


class OpenAIProvider(OpenAICompatibleProvider):
    """Proveedor para OpenAI."""

    def _get_api_key(self) -> Optional[str]:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            logger.warning("OPENAI_API_KEY no encontrada")
        return key

    def _setup_client(self):
        self._setup_openai_client(self.api_key)

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        return self._openai_generate_content("OpenAI", "gpt-4", system_prompt, prompt=prompt, **kwargs)


class AnthropicProvider(LLMProvider):
    """Proveedor para Anthropic (Claude)."""

    def _get_api_key(self) -> Optional[str]:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            logger.warning("ANTHROPIC_API_KEY no encontrada")
        return key

    def _setup_client(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            logger.error("Biblioteca anthropic no instalada. Instala con: pip install anthropic")
            self.client = None

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        if not self.client: return None

        system_content = system_prompt or "Eres un experto en métodos matemáticos para física e ingeniería."
        model = self.model_name or "claude-3-opus-20240229"
        provider_name = self._get_provider_name()

        # Intentar caché primero
        if self.cache:
            cached = self.cache.get(prompt, provider_name, model)
            if cached:
                logger.info(f"[{provider_name}] Contenido obtenido del caché (modelo={model})")
                return cached

        # Generar respuesta
        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                system=system_content,
                messages=[{"role": "user", "content": prompt}]
            )
            content = message.content[0].text.strip()
            logger.info(f"[{provider_name}] Contenido generado exitosamente (modelo={model}, longitud={len(content)})")

            # Guardar en caché
            if self.cache:
                metadata = {
                    'provider': provider_name,
                    'model': model,
                    'temperature': kwargs.get("temperature", 0.7),
                    'max_tokens': kwargs.get("max_tokens", 2000)
                }
                self.cache.put(prompt, provider_name, model, content, metadata=metadata)

            return content
        except Exception as e:
            logger.error(f"[{provider_name}] Error llamando a Anthropic API: {e}")
            return None


class GeminiProvider(LLMProvider):
    """Proveedor para Google Gemini."""

    def _get_api_key(self) -> Optional[str]:
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            logger.warning("GOOGLE_API_KEY no encontrada")
        return key

    def _setup_client(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            logger.error("Biblioteca google-generativeai no instalada")
            self.genai = None

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        if not self.genai: return None

        model_name = self.model_name or "gemini-2.5-pro"
        if model_name == 'gemini': model_name = "gemini-2.5-pro"
        provider_name = self._get_provider_name()

        # Intentar caché primero
        if self.cache:
            cached = self.cache.get(prompt, provider_name, model_name)
            if cached:
                logger.info(f"[{provider_name}] Contenido obtenido del caché (modelo={model_name})")
                return cached

        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": kwargs.get("max_tokens", 8192),
            "response_mime_type": "text/plain",
        }

        # Generar respuesta
        try:
            model_instance = self.genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                # System instructions can be passed to model if supported, 
                # or prepended to prompt. Gemini 1.5 supports system_instruction arg.
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(prompt)
            content = response.text
            logger.info(f"[{provider_name}] Contenido generado exitosamente (modelo={model_name}, longitud={len(content)})")

            # Guardar en caché
            if self.cache:
                metadata = {
                    'provider': provider_name,
                    'model': model_name,
                    'temperature': kwargs.get("temperature", 0.7),
                    'max_tokens': kwargs.get("max_tokens", 8192)
                }
                self.cache.put(prompt, provider_name, model_name, content, metadata=metadata)

            return content
        except Exception as e:
            logger.error(f"[{provider_name}] Error llamando a Gemini API: {e}")
            return None


class LocalProvider(OpenAICompatibleProvider):
    """Proveedor para modelos locales (Ollama/LM Studio) vía OpenAI compatible API."""

    def __init__(self, model_name: Optional[str] = None, base_url: str = "http://localhost:11434/v1", cache: Optional['LLMCache'] = None):
        super().__init__(model_name, base_url=base_url, timeout=300.0, cache=cache)

    def _get_api_key(self) -> Optional[str]:
        return "not-needed"

    def _setup_client(self):
        self._setup_openai_client(self.api_key, base_url=self.base_url, timeout=self.timeout)

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        return self._openai_generate_content("Local", "llama3", system_prompt, prompt=prompt, **kwargs)


class DeepSeekProvider(OpenAICompatibleProvider):
    """Proveedor para DeepSeek (OpenAI-compatible)."""

    def __init__(self, model_name: Optional[str] = None, cache: Optional['LLMCache'] = None):
        super().__init__(model_name, base_url="https://api.deepseek.com", cache=cache)

    def _get_api_key(self) -> Optional[str]:
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            logger.warning("DEEPSEEK_API_KEY no encontrada")
        return key

    def _setup_client(self):
        self._setup_openai_client(self.api_key, base_url=self.base_url)

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        return self._openai_generate_content("DeepSeek", "deepseek-chat", system_prompt, prompt=prompt, **kwargs)


class GenericProvider(OpenAICompatibleProvider):
    """Proveedor Genérico Compatible con OpenAI (Groq, Mistral, etc)."""

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None, cache: Optional['LLMCache'] = None):
        super().__init__(model_name, base_url=base_url or os.getenv("GENERIC_BASE_URL"), cache=cache)

    def _get_api_key(self) -> Optional[str]:
        key = os.getenv("GENERIC_API_KEY")
        if not key:
            logger.warning("GENERIC_API_KEY no encontrada")
        return key

    def _setup_client(self):
        if not self.base_url:
            logger.warning("GENERIC_BASE_URL no definida")
        self._setup_openai_client(self.api_key, base_url=self.base_url)

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        default_system_prompt = self.DEFAULT_SYSTEM_PROMPT
        default_model = os.getenv("GENERIC_MODEL") or "gpt-3.5-turbo"
        return self._openai_generate_content("Generic", default_model, system_prompt or default_system_prompt, prompt=prompt, **kwargs)


def get_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Factory method para obtener un proveedor."""
    if provider_name == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_name == "anthropic":
        return AnthropicProvider(**kwargs)
    elif provider_name == "gemini":
        return GeminiProvider(**kwargs)
    elif provider_name == "local":
        return LocalProvider(**kwargs)
    elif provider_name == "deepseek":
        return DeepSeekProvider(**kwargs)
    elif provider_name == "generic":
        return GenericProvider(**kwargs)
    else:
        raise ValueError(f"Proveedor desconocido: {provider_name}")
