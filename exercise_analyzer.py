"""
Analizador de complejidad de ejercicios.
Identifica tipo, pasos, conceptos y variables de ejercicios.
"""
import re
from typing import Dict, List, Set
from collections import Counter

try:
    from utils.math_extractor import (
        extract_math_expressions,
        extract_variables,
        count_math_operations,
        estimate_complexity
    )
except ImportError:
    from .utils.math_extractor import (
        extract_math_expressions,
        extract_variables,
        count_math_operations,
        estimate_complexity
    )


class ExerciseAnalyzer:
    """Analiza la complejidad y estructura de ejercicios."""

    # Palabras clave para identificación de tipo
    DEMOSTRACION_KEYWORDS = [
        'demuestre', 'demuestre que', 'pruebe', 'verifique', 'muestre que'
    ]

    CALCULO_KEYWORDS = [
        'calcule', 'calcular', 'encuentre', 'determine', 'evalúe', 'evaluar'
    ]

    APLICACION_KEYWORDS = [
        'considere', 'suponga', 'modelo', 'sistema físico', 'aplicación',
        'dispositivo', 'campo', 'potencial'
    ]

    STEP_KEYWORDS = [
        'primero', 'luego', 'finalmente', 'ahora', 'a continuación',
        'por tanto', 'por lo tanto', 'en consecuencia', 'así',
        'por otro lado', 'además', 'también'
    ]

    # Patrones compilados para búsqueda eficiente
    TYPE_PATTERNS = {
        'demostracion': re.compile('|'.join(map(re.escape, DEMOSTRACION_KEYWORDS)), re.IGNORECASE),
        'calculo': re.compile('|'.join(map(re.escape, CALCULO_KEYWORDS)), re.IGNORECASE),
        'aplicacion': re.compile('|'.join(map(re.escape, APLICACION_KEYWORDS)), re.IGNORECASE)
    }

    STEP_KEYWORDS_PATTERN = re.compile('|'.join(map(re.escape, STEP_KEYWORDS)), re.IGNORECASE)

    # Conceptos matemáticos comunes
    CONCEPT_PATTERNS = {
        'vector_operations': [
            r'\\vec', r'\\cdot', r'\\times', r'\\nabla',
            r'producto\s+(escalar|vectorial)', r'gradiente', r'divergencia', r'rotacional'
        ],
        'coordinate_systems': [
            r'coordenadas?\s+(cartesianas?|polares?|cilíndricas?|esféricas?|toroidales?)',
            r'\\rho', r'\\theta', r'\\phi', r'\\hat\{e\}_'
        ],
        'integrals': [
            r'\\int', r'\\oint', r'integral', r'teorema\s+(de\s+)?(Green|Stokes|Gauss)',
            r'divergencia', r'rotacional'
        ],
        'differential_equations': [
            r'\\frac\{d', r'\\partial', r'ecuaci[óo]n\s+diferencial',
            r'EDP', r'EDO'
        ],
        'linear_algebra': [
            r'\\begin\{matrix\}', r'\\begin\{pmatrix\}', r'\\begin\{bmatrix\}',
            r'matriz', r'\\mathbf', r'autovalor', r'autovector'
        ],
        'complex_numbers': [
            r'\\mathbb\{C\}', r'z\s*=', r'n[úu]mero\s+complejo',
            r'\\Re', r'\\Im', r'\\arg'
        ],
        'series_expansions': [
            r'\\sum', r'serie', r'expansi[óo]n', r'Fourier',
            r'Taylor', r'\\sum_\{n=0\}'
        ]
    }

    def __init__(self):
        """Inicializa el analizador."""
        pass

    def identify_exercise_type(self, content: str) -> str:
        """
        Identifica el tipo de ejercicio.

        Args:
            content: Contenido del ejercicio

        Returns:
            Tipo de ejercicio: 'demostracion', 'calculo', 'aplicacion', 'mixto'
        """
        has_demostracion = bool(self.TYPE_PATTERNS['demostracion'].search(content))
        has_calculo = bool(self.TYPE_PATTERNS['calculo'].search(content))
        has_aplicacion = bool(self.TYPE_PATTERNS['aplicacion'].search(content))

        if has_demostracion and (has_calculo or has_aplicacion):
            return 'mixto'
        elif has_demostracion:
            return 'demostracion'
        elif has_calculo:
            return 'calculo'
        elif has_aplicacion:
            return 'aplicacion'
        else:
            return 'calculo'  # Por defecto

    def count_solution_steps(self, solution_content: str) -> int:
        """
        Cuenta el número de pasos en una solución.

        Busca indicadores de pasos como:
        - Numeración (1., 2., etc.)
        - Palabras clave (Primero, Luego, Finalmente, etc.)
        - Bloques de ecuaciones separados

        Args:
            solution_content: Contenido de la solución

        Returns:
            Número estimado de pasos
        """
        if not solution_content:
            return 0

        # Contar numeración explícita
        numbered_steps = len(re.findall(r'^\s*\d+[\.\)]\s+', solution_content, re.MULTILINE))

        # Contar palabras clave de pasos
        keyword_steps = len(self.STEP_KEYWORDS_PATTERN.findall(solution_content))

        # Contar bloques de ecuaciones (align, equation)
        equation_blocks = len(re.findall(
            r'\\begin\{(align|equation|aligned|eqnarray)\}',
            solution_content
        ))

        # Estimar pasos basado en separadores
        separators = len(re.findall(r'\n\n+', solution_content))

        # Tomar el máximo de los métodos
        estimated_steps = max(
            numbered_steps,
            keyword_steps // 2,  # Dividir porque pueden repetirse
            equation_blocks,
            separators // 2
        )

        return max(1, estimated_steps)  # Mínimo 1 paso

    def identify_concepts(self, content: str) -> Set[str]:
        """
        Identifica conceptos matemáticos presentes en el contenido.

        Args:
            content: Contenido a analizar

        Returns:
            Conjunto de conceptos identificados
        """
        concepts = set()

        for concept_name, patterns in self.CONCEPT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    concepts.add(concept_name)
                    break

        return concepts

    def analyze(self, exercise: Dict) -> Dict:
        """
        Analiza un ejercicio completo y retorna metadatos de complejidad.

        Args:
            exercise: Diccionario con información del ejercicio
                - 'content': Contenido del ejercicio
                - 'solution': Contenido de la solución (opcional)

        Returns:
            Diccionario con análisis de complejidad
        """
        content = exercise.get('content', '')
        solution = exercise.get('solution', '')

        # Extraer expresiones matemáticas
        math_expressions = extract_math_expressions(content)
        if solution:
            math_expressions.extend(extract_math_expressions(solution))

        # Extraer variables
        variables = extract_variables(math_expressions)

        # Identificar tipo
        exercise_type = self.identify_exercise_type(content)

        # Contar pasos en solución
        solution_steps = self.count_solution_steps(solution) if solution else 0

        # Identificar conceptos
        all_content = content + '\n' + (solution or '')
        concepts = self.identify_concepts(all_content)

        # Calcular complejidad matemática
        math_complexity = estimate_complexity(math_expressions)

        # Contar operaciones
        total_operations = {
            'integrals': 0,
            'derivatives': 0,
            'sums': 0,
            'vectors': 0,
            'matrices': 0,
            'functions': 0
        }
        for expr in math_expressions:
            ops = count_math_operations(expr)
            for key in total_operations:
                total_operations[key] += ops[key]

        # Calcular complejidad total
        total_complexity = (
            math_complexity +
            solution_steps * 2.0 +
            len(variables) * 0.5 +
            len(concepts) * 1.5 +
            sum(total_operations.values()) * 0.5
        )

        return {
            'type': exercise_type,
            'solution_steps': solution_steps,
            'variables': list(variables),
            'num_variables': len(variables),
            'concepts': list(concepts),
            'num_concepts': len(concepts),
            'math_complexity': math_complexity,
            'operations': total_operations,
            'total_complexity': total_complexity,
            'num_math_expressions': len(math_expressions)
        }
