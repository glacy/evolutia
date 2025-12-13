"""
Validador de complejidad.
Verifica que las variaciones generadas sean más complejas que los originales.
"""
import logging
from typing import Dict

try:
    from exercise_analyzer import ExerciseAnalyzer
    from utils.math_extractor import extract_math_expressions, estimate_complexity
except ImportError:
    from .exercise_analyzer import ExerciseAnalyzer
    from .utils.math_extractor import extract_math_expressions, estimate_complexity


logger = logging.getLogger(__name__)


class ComplexityValidator:
    """Valida que las variaciones sean más complejas que los originales."""
    
    def __init__(self):
        """Inicializa el validador."""
        self.analyzer = ExerciseAnalyzer()
    
    def validate(self, original_exercise: Dict, original_analysis: Dict, 
                 variation: Dict) -> Dict:
        """
        Valida que la variación sea más compleja que el original.
        
        Args:
            original_exercise: Ejercicio original
            original_analysis: Análisis del ejercicio original
            variation: Variación generada (debe tener 'variation_content')
        
        Returns:
            Diccionario con resultado de validación:
            - 'is_valid': bool
            - 'variation_analysis': análisis de la variación
            - 'improvements': lista de mejoras detectadas
            - 'warnings': lista de advertencias
        """
        variation_content = variation.get('variation_content', '')
        variation_solution = variation.get('variation_solution', '')
        
        if not variation_content:
            return {
                'is_valid': False,
                'reason': 'Variación sin contenido',
                'variation_analysis': None,
                'improvements': [],
                'warnings': ['Variación generada está vacía']
            }
        
        # Analizar la variación
        variation_exercise = {
            'content': variation_content,
            'solution': variation_solution
        }
        variation_analysis = self.analyzer.analyze(variation_exercise)
        
        # Comparar métricas
        improvements = []
        warnings = []
        
        # Comparar complejidad total
        original_complexity = original_analysis.get('total_complexity', 0)
        variation_complexity = variation_analysis.get('total_complexity', 0)
        
        if variation_complexity > original_complexity * 1.1:  # Al menos 10% más complejo
            improvements.append(
                f"Complejidad total aumentó de {original_complexity:.2f} a {variation_complexity:.2f}"
            )
        elif variation_complexity < original_complexity:
            warnings.append(
                f"Complejidad total disminuyó de {original_complexity:.2f} a {variation_complexity:.2f}"
            )
        
        # Comparar número de pasos
        original_steps = original_analysis.get('solution_steps', 0)
        variation_steps = variation_analysis.get('solution_steps', 0)
        
        if variation_steps > original_steps:
            improvements.append(
                f"Número de pasos aumentó de {original_steps} a {variation_steps}"
            )
        elif variation_steps < original_steps and original_steps > 0:
            warnings.append(
                f"Número de pasos disminuyó de {original_steps} a {variation_steps}"
            )
        
        # Comparar número de variables
        original_vars = original_analysis.get('num_variables', 0)
        variation_vars = variation_analysis.get('num_variables', 0)
        
        if variation_vars > original_vars:
            improvements.append(
                f"Número de variables aumentó de {original_vars} a {variation_vars}"
            )
        
        # Comparar número de conceptos
        original_concepts = original_analysis.get('num_concepts', 0)
        variation_concepts = variation_analysis.get('num_concepts', 0)
        
        if variation_concepts > original_concepts:
            improvements.append(
                f"Número de conceptos aumentó de {original_concepts} a {variation_concepts}"
            )
        
        # Comparar complejidad matemática
        original_math = original_analysis.get('math_complexity', 0)
        variation_math = variation_analysis.get('math_complexity', 0)
        
        if variation_math > original_math * 1.1:
            improvements.append(
                f"Complejidad matemática aumentó de {original_math:.2f} a {variation_math:.2f}"
            )
        elif variation_math < original_math:
            warnings.append(
                f"Complejidad matemática disminuyó de {original_math:.2f} a {variation_math:.2f}"
            )
        
        # Comparar operaciones
        original_ops = original_analysis.get('operations', {})
        variation_ops = variation_analysis.get('operations', {})
        
        for op_type in ['integrals', 'derivatives', 'sums', 'vectors', 'matrices']:
            orig_count = original_ops.get(op_type, 0)
            var_count = variation_ops.get(op_type, 0)
            if var_count > orig_count:
                improvements.append(
                    f"Operaciones de {op_type} aumentaron de {orig_count} a {var_count}"
                )
        
        # Determinar si es válida
        # Requisitos mínimos:
        # 1. Complejidad total debe ser mayor
        # 2. Al menos una métrica debe mejorar significativamente
        is_valid = (
            variation_complexity > original_complexity and
            len(improvements) >= 2
        )
        
        if not is_valid and len(warnings) > 0:
            warnings.append("La variación no cumple con los requisitos mínimos de complejidad")
        
        return {
            'is_valid': is_valid,
            'variation_analysis': variation_analysis,
            'improvements': improvements,
            'warnings': warnings,
            'original_complexity': original_complexity,
            'variation_complexity': variation_complexity,
            'complexity_increase': variation_complexity - original_complexity,
            'complexity_increase_percent': (
                (variation_complexity - original_complexity) / original_complexity * 100
                if original_complexity > 0 else 0
            )
        }
    
    def validate_batch(self, exercises_and_variations: list) -> list:
        """
        Valida un lote de variaciones.
        
        Args:
            exercises_and_variations: Lista de tuplas (ejercicio_original, análisis_original, variación)
        
        Returns:
            Lista de resultados de validación
        """
        results = []
        
        for original_exercise, original_analysis, variation in exercises_and_variations:
            result = self.validate(original_exercise, original_analysis, variation)
            results.append(result)
            
            if result['is_valid']:
                logger.info(f"Variación válida: {len(result['improvements'])} mejoras detectadas")
            else:
                logger.warning(f"Variación inválida: {result.get('reason', 'Complejidad insuficiente')}")
        
        return results

