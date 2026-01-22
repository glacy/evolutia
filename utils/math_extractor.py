"""
Utilidades para extraer y analizar expresiones matemáticas de archivos Markdown.
"""
import re
from typing import List, Dict, Set

# Patrones comunes para variables
# Variables latinas: \vec{A}, A, \mathbf{B}, etc.
LATIN_PATTERN = re.compile(r'\\vec\{([A-Za-z])\}|\\mathbf\{([A-Za-z])\}|\\hat\{([A-Za-z])\}|([A-Za-z])(?![a-z])')

# Letras griegas: \alpha, \beta, \theta, etc.
GREEK_PATTERN = re.compile(r'\\(alpha|beta|gamma|delta|epsilon|theta|phi|rho|omega|sigma|lambda|mu|nu|pi|tau)')


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
    expressions = []

    # 1. Bloques math de MyST: :::{math} ... :::
    # Se procesan primero y se eliminan del contenido para evitar duplicados si contienen $ o $$
    math_block_pattern = r':::\{math\}\s*(.*?)\s*:::'
    for match in re.finditer(math_block_pattern, content, re.DOTALL):
        expr = match.group(1).strip()
        if expr:
            expressions.append(expr)
    content = re.sub(math_block_pattern, '', content, flags=re.DOTALL)

    # 2. Expresiones display: $$...$$ o \[...\]
    display_pattern = r'\$\$([^$]+)\$\$|\\\[([^\]]+)\\\]'
    for match in re.finditer(display_pattern, content, re.DOTALL):
        expr = match.group(1) or match.group(2)
        if expr:
            expressions.append(expr.strip())
    content = re.sub(display_pattern, '', content, flags=re.DOTALL)

    # 3. Expresiones inline: $...$ o \(...\)
    inline_pattern = r'\$([^$]+)\$|\\\(([^\)]+)\\\)'
    for match in re.finditer(inline_pattern, content):
        expr = match.group(1) or match.group(2)
        if expr:
            expressions.append(expr.strip())

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
        # Buscar variables latinas
        for match in LATIN_PATTERN.finditer(expr):
            var = match.group(1) or match.group(2) or match.group(3) or match.group(4)
            if var and var.isalpha():
                variables.add(var)

        # Buscar letras griegas
        for match in GREEK_PATTERN.finditer(expr):
            variables.add(match.group(1))

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
        'integrals': len(re.findall(r'\\int|\\oint', expression)),
        'derivatives': len(re.findall(r'\\partial|\\nabla|\\frac\{d', expression)),
        'sums': len(re.findall(r'\\sum|\\prod', expression)),
        'vectors': len(re.findall(r'\\vec|\\mathbf', expression)),
        'matrices': len(re.findall(r'\\begin\{matrix\}|\\begin\{pmatrix\}|\\begin\{bmatrix\}', expression)),
        'functions': len(re.findall(r'\\sin|\\cos|\\tan|\\exp|\\log|\\ln', expression)),
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

    for expr in expressions:
        # Longitud de la expresión
        total_complexity += len(expr) * 0.01

        # Operaciones complejas
        ops = count_math_operations(expr)
        total_complexity += ops['integrals'] * 2.0
        total_complexity += ops['derivatives'] * 1.5
        total_complexity += ops['sums'] * 1.5
        total_complexity += ops['vectors'] * 1.0
        total_complexity += ops['matrices'] * 2.5
        total_complexity += ops['functions'] * 0.5

        # Número de variables
        vars_count = len(extract_variables([expr]))
        total_complexity += vars_count * 0.3

        # Bloques align (ecuaciones múltiples)
        if '\\begin{align' in expr or '\\begin{aligned' in expr:
            total_complexity += 2.0

    return total_complexity
