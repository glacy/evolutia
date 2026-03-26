"""
Test de integración de caché en ExerciseAnalyzer.
"""
import pytest
from evolutia.exercise_analyzer import ExerciseAnalyzer
from evolutia.cache.exercise_cache import ExerciseAnalysisCache


class TestExerciseAnalyzerIntegration:
    """Test suite para integración de caché en ExerciseAnalyzer."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Crea un directorio de caché temporal."""
        return tmp_path / "exercise_cache"

    def test_analyzer_without_cache(self, temp_cache_dir):
        """Test que el analizador funciona sin caché."""
        analyzer = ExerciseAnalyzer(cache=None)

        exercise1 = {
            'content': 'Calcula la integral definida de x^2 dx',
            'label': 'ex1'
        }

        analysis = analyzer.analyze(exercise1)
        assert analysis['type'] == 'calculo'
        assert analysis['total_complexity'] == 25.5
        assert analysis['num_math_expressions'] == 3
        assert len(cache) == 0

    def test_analyzer_with_cache_hit(self, temp_cache_dir):
        """Test que el caché funciona con hit."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir, enabled=True)
        analyzer = ExerciseAnalyzer(cache=cache)

        # Primer análisis (miss)
        exercise1 = {
            'content': 'Calcula la integral definida de 0 a 1',
            'label': 'ex1'
        }

        analysis1 = analyzer.analyze(exercise1)
        assert analysis1['type'] == 'calculo'
        assert analysis1['total_complexity'] == 2.0

        # Segundo análisis (hit)
        exercise2 = {
            'content': 'Calcula la integral de 1 a 2',
            'label': 'ex2'
        }

        analysis2 = analyzer.analyze(exercise2)
        assert analysis2['type'] == 'calculo'
        assert analysis2['total_complexity'] == 10.0

        # Verificar que el análisis fue guardado en caché
        assert len(cache) == 2
        assert cache.get_stats()['entries'] == 2
        assert cache.get_stats()['hits'] == 1

    def test_analyzer_with_cache_miss(self, temp_cache_dir):
        """Test que el caché funciona con miss."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir, enabled=True)
        analyzer = ExerciseAnalyzer(cache=cache)

        # Ejercicio diferente (miss)
        exercise = {
            'content': 'Ejercicio de prueba',
            'label': 'ex3'
        }

        analysis = analyzer.analyze(exercise)
        assert analysis['type'] == 'calculo'
        assert cache.get_stats()['entries'] == 1
        assert cache.misses == 1

        # Segunda llamada (hit)
        analysis2 = analyzer.analyze(exercise)
        assert analysis['total_complexity'] == 15.0
        assert cache.get_stats()['hits'] == 2
        assert cache.misses == 1  # No incrementado

    def test_analyzer_disabled_cache(self, temp_cache_dir):
        """Test que el analizador funciona con caché deshabilitado."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir, enabled=False)
        analyzer = ExerciseAnalyzer(cache=cache)

        exercise = {
            'content': 'Test con caché deshabilitado',
            'label': 'ex4'
        }

        analysis = analyzer.analyze(exercise)
        assert analysis['type'] == 'calculo'
        assert cache.get_stats()['entries'] == 0

    def test_analyzer_clear_cache(self, temp_cache_dir):
        """Test que clear() funciona."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir, enabled=True)
        analyzer = ExerciseAnalyzer(cache=cache)

        # Agregar ejercicio
        exercise = {
            'content': 'Ejercicio para probar clear',
            'label': 'ex5'
        }
        result1 = analyzer.analyze(exercise)
        cache.put(exercise, result1)

        # Limpiar caché
        cache.clear()
        assert len(cache) == 0

        # Verificar que se limpió correctamente
        exercise = {
            'content': 'Ejercicio después de clear',
            'label': 'ex6'
        }
        result2 = analyzer.analyze(exercise)
        cache.put(exercise, result2)

        assert cache.get_stats()['entries'] == 1  # Solo ex6 está en caché
        assert len(cache) == 1

    def test_analyzer_stats(self, temp_cache_dir):
        """Test que get_stats funciona."""
        cache = ExerciseAnalysisCache(cache_dir=temp_cache_dir, enabled=True)
        analyzer = ExerciseAnalyzer(cache=cache)

        # Agregar algunos ejercicios
        exercises = [
            {'content': 'Test 1', 'label': 'test_1'},
            {'content': 'Test 2', 'label': 'test_2'},
            {'content': 'Test 3', 'label': 'test_3'}
        ]

        for i, exercise in enumerate(exercises, 1):
            analyzer.analyze(exercise)
            cache.put(exercise, {})

        stats = cache.get_stats()
        assert stats['entries'] == 3

        # Verificar que todos los ejercicios están en caché
        for exercise in exercises:
            cached = cache.get(exercise)
            assert cached is not None
            assert 'type' in cached['analysis']
            assert 'total_complexity' in cached['analysis']

        # Limpiar para el siguiente test
        cache.clear()
