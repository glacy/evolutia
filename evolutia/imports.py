"""
Módulo de imports centralizados y condicionales para EvolutIA.
Gestiona imports de dependencias opcionales (RAG, ML, etc.) de forma centralizada.
"""
import logging

logger = logging.getLogger(__name__)


class OptionalImports:
    """
    Gestor de imports opcionales para EvolutIA.

    Permite importar dependencias opcionales de forma controlada,
    con mensajes de error claros cuando no están disponibles.
    """

    _imported_modules = {}

    @classmethod
    def get_chromadb(cls):
        """Importa ChromaDB si está disponible."""
        if 'chromadb' in cls._imported_modules:
            return cls._imported_modules['chromadb']

        try:
            import chromadb
            from chromadb.config import Settings
            cls._imported_modules['chromadb'] = (chromadb, Settings)
            logger.debug("[OptionalImports] ChromaDB importado exitosamente")
            return chromadb, Settings
        except ImportError:
            logger.warning(
                "[OptionalImports] chromadb no está instalado. "
                "Instala con: pip install -e '.[rag]'"
            )
            return None, None

    @classmethod
    def get_sentence_transformers(cls):
        """Importa sentence-transformers si está disponible."""
        if 'sentence_transformers' in cls._imported_modules:
            return cls._imported_modules['sentence_transformers']

        try:
            from sentence_transformers import SentenceTransformer
            cls._imported_modules['sentence_transformers'] = SentenceTransformer
            logger.debug("[OptionalImports] sentence-transformers importado exitosamente")
            return SentenceTransformer
        except ImportError:
            logger.warning(
                "[OptionalImports] sentence-transformers no está instalado. "
                "Instala con: pip install -e '.[rag]'"
            )
            return None

    @classmethod
    def get_openai(cls):
        """Importa OpenAI si está disponible."""
        if 'openai' in cls._imported_modules:
            return cls._imported_modules['openai']

        try:
            from openai import OpenAI
            cls._imported_modules['openai'] = OpenAI
            logger.debug("[OptionalImports] OpenAI importado exitosamente")
            return OpenAI
        except ImportError:
            logger.warning(
                "[OptionalImports] openai no está instalado. "
                "Instala con: pip install openai"
            )
            return None

    @classmethod
    def get_anthropic(cls):
        """Importa Anthropic si está disponible."""
        if 'anthropic' in cls._imported_modules:
            return cls._imported_modules['anthropic']

        try:
            import anthropic
            cls._imported_modules['anthropic'] = anthropic
            logger.debug("[OptionalImports] Anthropic importado exitosamente")
            return anthropic
        except ImportError:
            logger.warning(
                "[OptionalImports] anthropic no está instalado. "
                "Instala con: pip install anthropic"
            )
            return None

    @classmethod
    def get_google_generativeai(cls):
        """Importa google-generativeai si está disponible."""
        if 'google_generativeai' in cls._imported_modules:
            return cls._imported_modules['google_generativeai']

        try:
            import google.generativeai as genai
            cls._imported_modules['google_generativeai'] = genai
            logger.debug("[OptionalImports] google-generativeai importado exitosamente")
            return genai
        except ImportError:
            logger.warning(
                "[OptionalImports] google-generativeai no está instalado. "
                "Instala con: pip install google-generativeai"
            )
            return None

    @classmethod
    def check_rag_available(cls) -> bool:
        """Verifica si todas las dependencias de RAG están disponibles."""
        chromadb, _ = cls.get_chromadb()
        sentence_transformers = cls.get_sentence_transformers()

        if chromadb is None or sentence_transformers is None:
            return False
        return True

    @classmethod
    def get_module(cls, module_name: str):
        """
        Importa un módulo específico por nombre.

        Args:
            module_name: Nombre del módulo a importar

        Returns:
            El módulo importado o None si no está disponible
        """
        if module_name in cls._imported_modules:
            return cls._imported_modules[module_name]

        try:
            module = __import__(module_name)
            cls._imported_modules[module_name] = module
            logger.debug(f"[OptionalImports] {module_name} importado exitosamente")
            return module
        except ImportError:
            logger.warning(f"[OptionalImports] {module_name} no está instalado.")
            return None


# Funciones de conveniencia para compatibilidad con código existente
def get_chromadb():
    """Importa ChromaDB si está disponible."""
    chromadb_module, settings = OptionalImports.get_chromadb()
    return chromadb_module, settings


def get_sentence_transformers():
    """Importa sentence-transformers si está disponible."""
    return OptionalImports.get_sentence_transformers()


def get_openai():
    """Importa OpenAI si está disponible."""
    return OptionalImports.get_openai()


def get_anthropic():
    """Importa Anthropic si está disponible."""
    return OptionalImports.get_anthropic()


def get_google_generativeai():
    """Importa google-generativeai si está disponible."""
    return OptionalImports.get_google_generativeai()


def check_rag_available() -> bool:
    """Verifica si todas las dependencias de RAG están disponibles."""
    return OptionalImports.check_rag_available()
