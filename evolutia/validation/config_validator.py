"""
Validador de configuración para EvolutIA.
Valida exhaustivamente la configuración del sistema.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Excepción para errores de validación de configuración."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []
        self.message = message


class ConfigValidator:
    """Validador de configuración del sistema."""

    # Valores válidos para algunas configuraciones
    VALID_API_PROVIDERS = {
        'openai', 'anthropic', 'local', 'gemini', 'deepseek', 'generic'
    }
    VALID_EMBEDDING_PROVIDERS = {'openai', 'sentence-transformers'}
    VALID_VECTOR_STORE_TYPES = {'chromadb'}

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida toda la configuración.

        Args:
            config: Diccionario de configuración

        Returns:
            Tupla (is_valid, error_messages) donde is_valid es True si la
            configuración es válida, y error_messages es una lista con
            mensajes de error (vacía si is_valid es True)
        """
        self.errors = []
        self.warnings = []

        # Validar secciones principales
        self._validate_paths(config.get('paths', {}))
        self._validate_api(config.get('api', {}))
        self._validate_exam(config.get('exam', {}))
        self._validate_generation(config.get('generation', {}))
        self._validate_rag(config.get('rag', {}))

        # Log warnings
        for warning in self.warnings:
            logger.warning(f"[ConfigValidator] {warning}")

        return len(self.errors) == 0, self.errors

    def _validate_paths(self, paths: Dict[str, Any]):
        """Valida la configuración de rutas."""
        if not paths:
            self.warnings.append("No se encontró configuración de rutas")
            return

        # Validar base_path
        base_path = paths.get('base_path')
        if base_path:
            path = Path(base_path)
            if not path.exists():
                self.errors.append(
                    f"paths.base_path no existe: {base_path}"
                )
            elif not path.is_dir():
                self.errors.append(
                    f"paths.base_path no es un directorio: {base_path}"
                )

        # Validar materials_directories
        materials_dirs = paths.get('materials_directories')
        if materials_dirs:
            if isinstance(materials_dirs, str) and materials_dirs == 'auto':
                # Valor especial para descubrimiento automático
                pass
            elif isinstance(materials_dirs, list):
                for topic in materials_dirs:
                    if base_path:
                        topic_path = Path(base_path) / topic
                        if not topic_path.exists():
                            self.warnings.append(
                                f"paths.materials_directories contiene tema no existente: {topic}"
                            )

    def _validate_api(self, api: Dict[str, Any]):
        """Valida la configuración de API."""
        if not api:
            self.warnings.append("No se encontró configuración de API")
            return

        # Validar default_provider
        default_provider = api.get('default_provider')
        if default_provider:
            if default_provider not in self.VALID_API_PROVIDERS:
                self.errors.append(
                    f"api.default_provider debe ser uno de {sorted(self.VALID_API_PROVIDERS)}, "
                    f"obtenido: {default_provider}"
                )

        # Validar configuración de proveedores
        providers = api.get('providers', {})
        if providers:
            for provider_name, provider_config in providers.items():
                if provider_name not in self.VALID_API_PROVIDERS:
                    self.warnings.append(
                        f"api.providers contiene proveedor desconocido: {provider_name}"
                    )
                    continue

                self._validate_provider_config(provider_name, provider_config)

    def _validate_provider_config(self, provider_name: str, provider_config: Dict[str, Any]):
        """Valida la configuración de un proveedor específico."""
        if provider_name == 'openai':
            self._validate_openai_config(provider_config)
        elif provider_name == 'anthropic':
            self._validate_anthropic_config(provider_config)
        elif provider_name == 'local':
            self._validate_local_config(provider_config)
        elif provider_name == 'gemini':
            self._validate_gemini_config(provider_config)
        elif provider_name == 'deepseek':
            self._validate_deepseek_config(provider_config)
        elif provider_name == 'generic':
            self._validate_generic_config(provider_config)

    def _validate_openai_config(self, config: Dict[str, Any]):
        """Valida configuración de OpenAI."""
        model = config.get('model')
        if model and not isinstance(model, str):
            self.errors.append(
                f"api.providers.openai.model debe ser string, obtenido: {type(model)}"
            )

        max_tokens = config.get('max_tokens')
        if max_tokens is not None:
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                self.errors.append(
                    f"api.providers.openai.max_tokens debe ser entero positivo, "
                    f"obtenido: {max_tokens}"
                )

        temperature = config.get('temperature')
        if temperature is not None:
            if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2):
                self.errors.append(
                    f"api.providers.openai.temperature debe estar entre 0 y 2, "
                    f"obtenido: {temperature}"
                )

    def _validate_anthropic_config(self, config: Dict[str, Any]):
        """Valida configuración de Anthropic."""
        model = config.get('model')
        if model and not isinstance(model, str):
            self.errors.append(
                f"api.providers.anthropic.model debe ser string, obtenido: {type(model)}"
            )

        max_tokens = config.get('max_tokens')
        if max_tokens is not None:
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                self.errors.append(
                    f"api.providers.anthropic.max_tokens debe ser entero positivo, "
                    f"obtenido: {max_tokens}"
                )

        temperature = config.get('temperature')
        if temperature is not None:
            if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 1):
                self.errors.append(
                    f"api.providers.anthropic.temperature debe estar entre 0 y 1, "
                    f"obtenido: {temperature}"
                )

    def _validate_local_config(self, config: Dict[str, Any]):
        """Valida configuración de modelos locales."""
        base_url = config.get('base_url')
        if base_url:
            if not isinstance(base_url, str):
                self.errors.append(
                    f"api.providers.local.base_url debe ser string, obtenido: {type(base_url)}"
                )
            elif not base_url.startswith(('http://', 'https://')):
                self.errors.append(
                    f"api.providers.local.base_url debe ser una URL válida, "
                    f"obtenido: {base_url}"
                )

        model = config.get('model')
        if model and not isinstance(model, str):
            self.errors.append(
                f"api.providers.local.model debe ser string, obtenido: {type(model)}"
            )

        timeout = config.get('timeout')
        if timeout is not None:
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                self.errors.append(
                    f"api.providers.local.timeout debe ser numérico positivo, "
                    f"obtenido: {timeout}"
                )

    def _validate_gemini_config(self, config: Dict[str, Any]):
        """Valida configuración de Gemini."""
        model = config.get('model')
        if model and not isinstance(model, str):
            self.errors.append(
                f"api.providers.gemini.model debe ser string, obtenido: {type(model)}"
            )

        temperature = config.get('temperature')
        if temperature is not None:
            if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2):
                self.errors.append(
                    f"api.providers.gemini.temperature debe estar entre 0 y 2, "
                    f"obtenido: {temperature}"
                )

    def _validate_deepseek_config(self, config: Dict[str, Any]):
        """Valida configuración de DeepSeek."""
        model = config.get('model')
        if model and not isinstance(model, str):
            self.errors.append(
                f"api.providers.deepseek.model debe ser string, obtenido: {type(model)}"
            )

        temperature = config.get('temperature')
        if temperature is not None:
            if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2):
                self.errors.append(
                    f"api.providers.deepseek.temperature debe estar entre 0 y 2, "
                    f"obtenido: {temperature}"
                )

    def _validate_generic_config(self, config: Dict[str, Any]):
        """Valida configuración genérica."""
        base_url = config.get('base_url')
        if base_url:
            if not isinstance(base_url, str):
                self.errors.append(
                    f"api.providers.generic.base_url debe ser string, obtenido: {type(base_url)}"
                )
            elif not base_url.startswith(('http://', 'https://')):
                self.errors.append(
                    f"api.providers.generic.base_url debe ser una URL válida, "
                    f"obtenido: {base_url}"
                )

        model = config.get('model')
        if model and not isinstance(model, str):
            self.errors.append(
                f"api.providers.generic.model debe ser string, obtenido: {type(model)}"
            )

    def _validate_exam(self, exam: Dict[str, Any]):
        """Valida la configuración de examen."""
        if not exam:
            self.warnings.append("No se encontró configuración de examen")
            return

        default = exam.get('default', {})
        if default:
            self._validate_exam_default(default)

        keywords = exam.get('keywords', {})
        if keywords:
            self._validate_exam_keywords(keywords)

    def _validate_exam_default(self, default: Dict[str, Any]):
        """Valida configuración por defecto de examen."""
        subject = default.get('subject')
        if subject and not isinstance(subject, str):
            self.errors.append(
                f"exam.default.subject debe ser string, obtenido: {type(subject)}"
            )

        points_per_exercise = default.get('points_per_exercise')
        if points_per_exercise is not None:
            if not isinstance(points_per_exercise, int) or points_per_exercise <= 0:
                self.errors.append(
                    f"exam.default.points_per_exercise debe ser entero positivo, "
                    f"obtenido: {points_per_exercise}"
                )

        duration_hours = default.get('duration_hours')
        if duration_hours is not None:
            if not isinstance(duration_hours, (int, float)) or not (0 < duration_hours <= 24):
                self.errors.append(
                    f"exam.default.duration_hours debe estar entre 0 y 24, "
                    f"obtenido: {duration_hours}"
                )

    def _validate_exam_keywords(self, keywords: Dict[str, Any]):
        """Valida configuración de keywords de examen."""
        if not isinstance(keywords, dict):
            self.errors.append(
                f"exam.keywords debe ser un diccionario, obtenido: {type(keywords)}"
            )
            return

        for topic, kw_list in keywords.items():
            if not isinstance(kw_list, list):
                self.errors.append(
                    f"exam.keywords.{topic} debe ser una lista, obtenido: {type(kw_list)}"
                )
            else:
                for kw in kw_list:
                    if not isinstance(kw, str):
                        self.errors.append(
                            f"exam.keywords.{topic} debe contener solo strings, "
                            f"encontrado: {kw} ({type(kw)})"
                        )

    def _validate_generation(self, generation: Dict[str, Any]):
        """Valida la configuración de generación."""
        if not generation:
            self.warnings.append("No se encontró configuración de generación")
            return

        max_workers = generation.get('max_workers')
        if max_workers is not None:
            if not isinstance(max_workers, int) or not (1 <= max_workers <= 50):
                self.errors.append(
                    f"generation.max_workers debe estar entre 1 y 50, "
                    f"obtenido: {max_workers}"
                )

        request_delay = generation.get('request_delay')
        if request_delay is not None:
            if not isinstance(request_delay, (int, float)) or request_delay < 0:
                self.errors.append(
                    f"generation.request_delay debe ser numérico no negativo, "
                    f"obtenido: {request_delay}"
                )

        retry_attempts = generation.get('retry_attempts')
        if retry_attempts is not None:
            if not isinstance(retry_attempts, int) or retry_attempts < 0:
                self.errors.append(
                    f"generation.retry_attempts debe ser entero no negativo, "
                    f"obtenido: {retry_attempts}"
                )

        llm_params = generation.get('llm_params', {})
        if llm_params:
            self._validate_llm_params(llm_params)

        complexity = generation.get('complexity', {})
        if complexity:
            self._validate_complexity_config(complexity)

    def _validate_llm_params(self, llm_params: Dict[str, Any]):
        """Valida parámetros LLM de generación."""
        default_temperature = llm_params.get('default_temperature')
        if default_temperature is not None:
            if not isinstance(default_temperature, (int, float)) or not (0 <= default_temperature <= 2):
                self.errors.append(
                    f"generation.llm_params.default_temperature debe estar entre 0 y 2, "
                    f"obtenido: {default_temperature}"
                )

        default_max_tokens = llm_params.get('default_max_tokens')
        if default_max_tokens is not None:
            if not isinstance(default_max_tokens, int) or default_max_tokens <= 0:
                self.errors.append(
                    f"generation.llm_params.default_max_tokens debe ser entero positivo, "
                    f"obtenido: {default_max_tokens}"
                )

    def _validate_complexity_config(self, complexity: Dict[str, Any]):
        """Valida configuración de complejidad."""
        min_improvement_percent = complexity.get('min_improvement_percent')
        if min_improvement_percent is not None:
            if not isinstance(min_improvement_percent, (int, float)) or not (0 <= min_improvement_percent <= 100):
                self.errors.append(
                    f"generation.complexity.min_improvement_percent debe estar entre 0 y 100, "
                    f"obtenido: {min_improvement_percent}"
                )

        required_improvements_count = complexity.get('required_improvements_count')
        if required_improvements_count is not None:
            if not isinstance(required_improvements_count, int) or required_improvements_count < 0:
                self.errors.append(
                    f"generation.complexity.required_improvements_count debe ser entero no negativo, "
                    f"obtenido: {required_improvements_count}"
                )

    def _validate_rag(self, rag: Dict[str, Any]):
        """Valida la configuración de RAG."""
        if not rag:
            return  # RAG es opcional

        vector_store = rag.get('vector_store', {})
        if vector_store:
            self._validate_rag_vector_store(vector_store)

        embeddings = rag.get('embeddings', {})
        if embeddings:
            self._validate_rag_embeddings(embeddings)

        retrieval = rag.get('retrieval', {})
        if retrieval:
            self._validate_rag_retrieval(retrieval)

        chunking = rag.get('chunking', {})
        if chunking:
            self._validate_rag_chunking(chunking)

    def _validate_rag_vector_store(self, vector_store: Dict[str, Any]):
        """Valida configuración de vector store RAG."""
        store_type = vector_store.get('type')
        if store_type and store_type not in self.VALID_VECTOR_STORE_TYPES:
            self.errors.append(
                f"rag.vector_store.type debe ser uno de {sorted(self.VALID_VECTOR_STORE_TYPES)}, "
                f"obtenido: {store_type}"
            )

        persist_directory = vector_store.get('persist_directory')
        if persist_directory:
            # Verificar que el directorio pueda crearse
            path = Path(persist_directory)
            if path.exists() and not path.is_dir():
                self.errors.append(
                    f"rag.vector_store.persist_directory debe ser un directorio, "
                    f"obtenido: {persist_directory}"
                )

    def _validate_rag_embeddings(self, embeddings: Dict[str, Any]):
        """Valida configuración de embeddings RAG."""
        provider = embeddings.get('provider')
        if provider and provider not in self.VALID_EMBEDDING_PROVIDERS:
            self.errors.append(
                f"rag.embeddings.provider debe ser uno de {sorted(self.VALID_EMBEDDING_PROVIDERS)}, "
                f"obtenido: {provider}"
            )

        model = embeddings.get('model')
        if model and not isinstance(model, str):
            self.errors.append(
                f"rag.embeddings.model debe ser string, obtenido: {type(model)}"
            )

        batch_size = embeddings.get('batch_size')
        if batch_size is not None:
            if not isinstance(batch_size, int) or batch_size <= 0:
                self.errors.append(
                    f"rag.embeddings.batch_size debe ser entero positivo, "
                    f"obtenido: {batch_size}"
                )

    def _validate_rag_retrieval(self, retrieval: Dict[str, Any]):
        """Valida configuración de recuperación RAG."""
        top_k = retrieval.get('top_k')
        if top_k is not None:
            if not isinstance(top_k, int) or not (1 <= top_k <= 100):
                self.errors.append(
                    f"rag.retrieval.top_k debe estar entre 1 y 100, "
                    f"obtenido: {top_k}"
                )

        similarity_threshold = retrieval.get('similarity_threshold')
        if similarity_threshold is not None:
            if not isinstance(similarity_threshold, (int, float)) or not (0 <= similarity_threshold <= 1):
                self.errors.append(
                    f"rag.retrieval.similarity_threshold debe estar entre 0 y 1, "
                    f"obtenido: {similarity_threshold}"
                )

    def _validate_rag_chunking(self, chunking: Dict[str, Any]):
        """Valida configuración de chunking RAG."""
        chunk_size = chunking.get('chunk_size')
        if chunk_size is not None:
            if not isinstance(chunk_size, int) or chunk_size <= 0:
                self.errors.append(
                    f"rag.chunking.chunk_size debe ser entero positivo, "
                    f"obtenido: {chunk_size}"
                )

        chunk_overlap = chunking.get('chunk_overlap')
        if chunk_overlap is not None:
            if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
                self.errors.append(
                    f"rag.chunking.chunk_overlap debe ser entero no negativo, "
                    f"obtenido: {chunk_overlap}"
                )

        if chunk_size and chunk_overlap and chunk_overlap >= chunk_size:
            self.errors.append(
                f"rag.chunking.chunk_overlap debe ser menor que chunk_size, "
                f"obtenido: overlap={chunk_overlap}, size={chunk_size}"
            )
