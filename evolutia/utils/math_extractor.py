"""
Utilidades para extraer y analizar expresiones matemáticas de archivos Markdown.
"""
import re
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

# Patrones comunes para variables
# Variables latinas: \vec{A}, A, \mathbf{B}, etc.
LATIN_REGEX = r'\\vec\{([A-Za-z])\}|\\mathbf\{([A-Za-z])\}|\\hat\{([A-Za-z])\}|([A-Za-z])(?![a-z])'

# Letras griegas: \alpha, \beta, \theta, etc.
GREEK_REGEX = r'\\(alpha|beta|gamma|delta|epsilon|theta|phi|rho|omega|sigma|lambda|mu|nu|pi|tau)'

# Combine patterns for faster extraction
COMBINED_VARIABLES_PATTERN = re.compile(f'{LATIN_REGEX}|{GREEK_REGEX}')

# Patrones compilados para operaciones matemáticas
INTEGRALS_PATTERN = re.compile(r'\\int|\\oint')
DERIVATIVES_PATTERN = re.compile(r'\\partial|\\nabla|\\frac\{d')
SUMS_PATTERN = re.compile(r'\\sum|\\prod')
VECTORS_PATTERN = re.compile(r'\\vec|\\mathbf')
MATRICES_PATTERN = re.compile(r'\\begin\{matrix\}|\\begin\{pmatrix\}|\\begin\{bmatrix\}')
FUNCTIONS_PATTERN = re.compile(r'\\sin|\\cos|\\tan|\\exp|\\log|\\ln')

# Combined pattern to extract all math expressions in one pass.
# Order matters: blocks first, then display, then inline to avoid incorrect nesting detection.
# DOTALL is needed for block content (.*?), and doesn't affect negations ([^$]+).
COMBINED_MATH_PATTERN = re.compile(
    r':::\{math\}\s*(?P<block_content>.*?)\s*:::|'
    r'\$\$(?P<display_dollar>[^$]+)\$\$|\\\[(?P<display_bracket>[^\]]+)\\\]|'
    r'\$(?P<inline_dollar>[^$]+)\$|\\\((?P<inline_paren>[^\)]+)\\\)',
    re.DOTALL
)


def extract_math_expressions(content: str) -> List[str]:
    r"""
    Extrae todas las expresiones matemáticas del contenido.

    Busca expresiones en formato LaTeX:
    - Inline: $...$ o \(...\)
    - Display: $$...$$ o \[...\]
    - Math blocks: :::{math} ... :::

    Args:
        content: Contenido Markdown

    Returns:
        Lista de expresiones matemáticas encontradas
    """
    if not content:
        return []

    expressions = []

    for match in COMBINED_MATH_PATTERN.finditer(content):
        expr = (
            match.group('block_content') or
            match.group('display_dollar') or
            match.group('display_bracket') or
            match.group('inline_dollar') or
            match.group('inline_paren')
        )
        if expr:
            expressions.append(expr.strip())

    logger.debug(f"[MathExtractor] Extraídas {len(expressions)} expresiones matemáticas del contenido")
    return expressions


def extract_variables(math_expressions: List[str]) -> Set[str]:
    """
    Extrae variables de expresiones matemáticas.

    Identifica letras griegas, variables latinas, y símbolos comunes.

    Args:
        math_expressions: Lista de expresiones matemáticas

    Returns:
        Conjunto de variables identificadas
    """
    variables = set()

    for expr in math_expressions:
        for match in COMBINED_VARIABLES_PATTERN.finditer(expr):
            # Check which group matched
            # lastindex gives the index of the capturing group that matched
            if match.lastindex:
                var = match.group(match.lastindex)
                if var:
                    variables.add(var)

    logger.debug(f"[MathExtractor] Extraídas {len(variables)} variables de {len(math_expressions)} expresiones")
    return variables


def count_math_operations(expression: str) -> Dict[str, int]:
    """
    Cuenta operaciones matemáticas en una expresión.

    Args:
        expression: Expresión matemática

    Returns:
        Diccionario con conteo de operaciones
    """
    operations = {
        'integrals': len(INTEGRALS_PATTERN.findall(expression)),
        'derivatives': len(DERIVATIVES_PATTERN.findall(expression)),
        'sums': len(SUMS_PATTERN.findall(expression)),
        'vectors': len(VECTORS_PATTERN.findall(expression)),
        'matrices': len(MATRICES_PATTERN.findall(expression)),
        'functions': len(FUNCTIONS_PATTERN.findall(expression)),
    }
    return operations


def estimate_complexity(expressions: List[str]) -> float:
    """
    Estima la complejidad matemática de un conjunto de expresiones.

    Args:
        expressions: Lista de expresiones matemáticas

    Returns:
        Puntuación de complejidad (mayor = más complejo)
    """
    if not expressions:
        return 0.0

    total_complexity = 0.0

    # Calcular operaciones en lote para mejorar rendimiento
    combined_expressions = " ".join(expressions)
    ops = count_math_operations(combined_expressions)

    total_complexity += ops['integrals'] * 2.0
    total_complexity += ops['derivatives'] * 1.5
    total_complexity += ops['sums'] * 1.5
    total_complexity += ops['vectors'] * 1.0
    total_complexity += ops['matrices'] * 2.5
    total_complexity += ops['functions'] * 0.5

    for expr in expressions:
        # Longitud de la expresión
        total_complexity += len(expr) * 0.01

        # Número de variables (por expresión para mantener lógica original)
        vars_count = len(extract_variables([expr]))
        total_complexity += vars_count * 0.3

        # Bloques align (ecuaciones múltiples)
        if '\\begin{align' in expr or '\\begin{aligned' in expr:
            total_complexity += 2.0

    logger.debug(f"[MathExtractor] Complejidad estimada: {total_complexity:.2f} (de {len(expressions)} expresiones)")
    return total_complexity
