"""
Tests para módulos de caché (LLMCache y ExerciseAnalysisCache).
"""
import pytest
import time
from evolutia.cache.llm_cache import LLMCache
from evolutia.cache.exercise_cache import ExerciseAnalysisCache


class TestLLMCache:
    """Test suite para LLMCache."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Crea un directorio de caché temporal."""
        return tmp_path / "llm_cache"

    def test_initialization(self, temp_cache_dir):
        """Test de inicialización de LLMCache."""
        cache = LLMCache(max_size=500, ttl_hours=1, persist_to_disk=True, cache_dir=temp_cache_dir)
        assert cache.max_size == 500
        assert cache.ttl == 1 * 3600
        assert cache.persist_to_disk is True
        assert temp_cache_dir.exists()

    def test_put_and_get(self, temp_cache_dir):
        """Test básico de put y get."""
        cache = LLMCache(cache_dir=temp_cache_dir)
        prompt = "Test prompt"
        provider = "openai"
        model = "gpt-4"
        response = "Test response with more than 20 characters"

        # 1. Cache miss
        assert cache.get(prompt, provider, model) is None
        assert cache.misses == 1

        # 2. Put
        cache.put(prompt, provider, model, response)

        # 3. Cache hit
        cached_response = cache.get(prompt, provider, model)
        assert cached_response == response
        assert cache.hits == 1

    def test_ttl_expiration(self, temp_cache_dir):
        """Test de expiración de TTL."""
        # Usar 1 segundo (aprox 0.00028 horas)
        cache = LLMCache(ttl_hours=0, persist_to_disk=False, cache_dir=temp_cache_dir)
        cache.ttl = 1  # 1 segundo de TTL

        prompt = "TTL test"
        provider = "openai"
        model = "gpt-4"
        response = "TTL response with more than 20 characters"

        cache.put(prompt, provider, model, response)
        time.sleep(1.1)  # Esperar más que el TTL

        assert cache.get(prompt, provider, model) is None
        assert len(cache) == 0

    def test_max_size_lru_eviction(self, temp_cache_dir):
        """Test de LRU eviction al alcanzar max_size."""
        cache = LLMCache(max_size=2, cache_dir=temp_cache_dir)

        # Agregar entrada 1
        cache.put("prompt1", "openai", "gpt-4", "Response 1 - Long response for LRU test")
        assert len(cache) == 1

        # Acceder a entrada 1 (no deberíase evictar)
        cache.get("prompt1", "openai", "gpt-4")
        assert len(cache) == 1

        # Agregar entrada 2 (caché lleno ahora)
        cache.put("prompt2", "openai", "gpt-4", "Response 2 - Long response for LRU test")
        assert len(cache) == 2

        # Agregar entrada 3 (deberíase evictar la más vieja)
        cache.put("prompt3", "openai", "gpt-4", "Response 3 - Long response for LRU test")
        assert len(cache) == 2

        # Verificar que la más vieja fue evictada (prompt1 ya no existe)
        assert cache.get("prompt1", "openai", "gpt-4") is None

        # Verificar que las otras dos aún existen
        assert cache.get("prompt2", "openai", "gpt-4") == "Response 2 - Long response for LRU test"
        assert cache.get("prompt3", "openai", "gpt-4") == "Response 3 - Long response for LRU test"

    def test_put_rejects_empty_or_error_responses(self, temp_cache_dir):
        """Test que put rechaza respuestas vacías o de error."""
        cache = LLMCache(cache_dir=temp_cache_dir)

        assert not cache.put("prompt", "openai", "gpt-4", "")
        assert not cache.put("prompt", "openai", "gpt-4", "  ")
        assert not cache.put("prompt", "openai", "gpt-4", "Lo siento, no puedo procesar tu solicitud.")
        assert not cache.put("prompt", "openai", "gpt-4", "Error: API call failed.")
        assert not cache.put("prompt", "openai", "gpt-4", "Corta")

        assert len(cache) == 0

    def test_clear_cache(self, temp_cache_dir):
        """Test de limpieza de caché."""
        cache = LLMCache(cache_dir=temp_cache_dir)
        cache.put("prompt1", "openai", "gpt-4", "Response with more than 20 characters for clear test")
        cache.put("prompt2", "openai", "gpt-4", "Second response with more than 20 characters for clear test")

        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0
        assert cache.get("prompt1", "openai", "gpt-4") is None

    def test_get_stats_and_hit_rate(self, temp_cache_dir):
        """Test de estadísticas y hit rate."""
        cache = LLMCache(cache_dir=temp_cache_dir)
        cache.put("p1", "o", "m", "Response with more than 20 characters for hit rate test")
        cache.put("p2", "o", "m", "Second response with more than 20 characters for hit rate test")

        cache.get("p1", "o", "m")
        cache.get("p2", "o", "m")
        cache.get("p3", "o", "m")

        stats = cache.get_stats()
        assert stats['entries'] == 2
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == pytest.approx(2 / 3)
        assert cache.hit_rate == pytest.approx(2 / 3)


class TestExerciseAnalysisCache:
    """Test suite para ExerciseAnalysisCache."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Crea un directorio de caché temporal."""
        return tmp_path / "exercise_cache"

    def test_initialization(self, temp_cache_dir):
        """Test de inicialización de ExerciseAnalysisCache."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir, enabled=True)
        assert cache.enabled is True
        assert temp_cache_dir.exists()

    def test_put_and_get(self, temp_cache_dir):
        """Test básico de put y get."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir)
        exercise = {"content": "Test exercise content", "label": "ex1"}
        analysis = {"total_complexity": 10.5, "concepts": ["calculus"]}

        # 1. Cache miss
        assert cache.get(exercise) is None
        assert cache.misses == 1

        # 2. Put
        assert cache.put(exercise, analysis)

        # 3. Cache hit
        cached_analysis = cache.get(exercise)
        assert cached_analysis is not None
        assert cached_analysis['analysis']['total_complexity'] == 10.5
        assert cache.hits == 1

    def test_disabled_cache(self, temp_cache_dir):
        """Test de caché deshabilitado."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir, enabled=False)
        exercise = {"content": "Test"}
        analysis = {"total_complexity": 5.0}

        assert cache.get(exercise) is None
        assert not cache.put(exercise, analysis)
        assert len(cache) == 0

    def test_put_rejects_incomplete_analysis(self, temp_cache_dir):
        """Test que put rechaza análisis incompletos."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir)
        exercise = {"content": "Test"}
        incomplete_analysis = {"concepts": ["calculus"]}

        assert not cache.put(exercise, incomplete_analysis)
        assert len(cache) == 0

    def test_clear_cache(self, temp_cache_dir):
        """Test de limpieza de caché."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir)
        exercise1 = {"content": "Test 1"}
        analysis1 = {"total_complexity": 1.0}
        exercise2 = {"content": "Test 2"}
        analysis2 = {"total_complexity": 2.0}

        cache.put(exercise1, analysis1)
        cache.put(exercise2, analysis2)

        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0
        assert cache.get(exercise1) is None

    def test_get_stats_and_hit_rate(self, temp_cache_dir):
        """Test de estadísticas y hit rate."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir)
        ex1 = {"content": "Ex 1"}
        an1 = {"total_complexity": 1}
        ex2 = {"content": "Ex 2"}
        an2 = {"total_complexity": 2}
        ex3 = {"content": "Ex 3"}

        cache.put(ex1, an1)
        cache.put(ex2, an2)

        cache.get(ex1)
        cache.get(ex2)
        cache.get(ex3)

        stats = cache.get_stats()
        assert stats['entries'] == 2
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == pytest.approx(2 / 3)
        assert cache.hit_rate == pytest.approx(2 / 3)
