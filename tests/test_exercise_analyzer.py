
import pytest
from exercise_analyzer import ExerciseAnalyzer

@pytest.fixture
def analyzer():
    return ExerciseAnalyzer()

def test_identify_exercise_type(analyzer):
    assert analyzer.identify_exercise_type("Demuestre que el teorema de Stokes...") == 'demostracion'
    assert analyzer.identify_exercise_type("Calcule la integral de línea...") == 'calculo'
    assert analyzer.identify_exercise_type("Considere un sistema físico donde...") == 'aplicacion'
    assert analyzer.identify_exercise_type("Demuestre y calcule el valor...") == 'mixto'

def test_count_solution_steps(analyzer):
    solution = """
    1. Primero, definimos las variables.
    2. Luego, aplicamos la fórmula.

    $$
    x = 5
    $$

    Finalmente, obtenemos el resultado.
    """
    steps = analyzer.count_solution_steps(solution)
    assert steps >= 2  # At least numbered steps

def test_identify_concepts(analyzer):
    content = r"Calcule la integral \int usando coordenadas esféricas y el gradiente \nabla"
    concepts = analyzer.identify_concepts(content)
    assert 'integrals' in concepts
    assert 'coordinate_systems' in concepts
    assert 'vector_operations' in concepts

def test_analyze(analyzer):
    exercise = {
        'content': r"Calcule $\int x dx$",
        'solution': r"1. $\frac{x^2}{2}$"
    }
    analysis = analyzer.analyze(exercise)

    assert analysis['type'] == 'calculo'
    assert analysis['solution_steps'] >= 1
    assert 'integrals' in analysis['concepts']
    assert analysis['math_complexity'] > 0
    assert analysis['total_complexity'] > 0
