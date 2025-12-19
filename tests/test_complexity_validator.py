
import pytest
from unittest.mock import MagicMock
from complexity_validator import ComplexityValidator

@pytest.fixture
def validator():
    val = ComplexityValidator()
    # Mock the analyzer to return controlled results
    val.analyzer = MagicMock()
    return val

def test_validate_valid_increase(validator):
    original_exercise = {'content': 'orig'}
    original_analysis = {
        'total_complexity': 10.0,
        'solution_steps': 2,
        'num_variables': 2,
        'num_concepts': 1,
        'math_complexity': 5.0,
        'operations': {'integrals': 0}
    }

    # Variation with increased complexity
    variation = {
        'variation_content': 'var',
        'variation_solution': 'sol'
    }

    validator.analyzer.analyze.return_value = {
        'total_complexity': 15.0, # > 11.0 (10 * 1.1) -> Improvement
        'solution_steps': 3,      # > 2 -> Improvement
        'num_variables': 3,       # > 2 -> Improvement
        'num_concepts': 2,        # > 1 -> Improvement
        'math_complexity': 6.0,   # > 5.5 -> Improvement
        'operations': {'integrals': 1} # > 0 -> Improvement
    }

    result = validator.validate(original_exercise, original_analysis, variation)

    assert result['is_valid'] is True
    assert len(result['improvements']) >= 2
    assert result['complexity_increase'] == 5.0

def test_validate_invalid_decrease(validator):
    original_exercise = {'content': 'orig'}
    original_analysis = {
        'total_complexity': 10.0,
        'solution_steps': 2
    }

    variation = {
        'variation_content': 'var',
        'variation_solution': 'sol'
    }

    # Variation with decreased complexity
    validator.analyzer.analyze.return_value = {
        'total_complexity': 8.0,
        'solution_steps': 1,
        'num_variables': 1,
        'num_concepts': 0,
        'math_complexity': 3.0,
        'operations': {}
    }

    result = validator.validate(original_exercise, original_analysis, variation)

    assert result['is_valid'] is False
    assert len(result['warnings']) > 0

def test_validate_batch(validator):
    validator.analyzer.analyze.return_value = {
        'total_complexity': 20.0,
        'solution_steps': 5,
        'num_variables': 5,
        'num_concepts': 2,
        'math_complexity': 10.0,
        'operations': {'integrals': 2}
    }

    batch = [
        ({'content': 'orig'}, {'total_complexity': 10.0}, {'variation_content': 'var'})
    ]

    results = validator.validate_batch(batch)
    assert len(results) == 1
    assert results[0]['is_valid'] is True
