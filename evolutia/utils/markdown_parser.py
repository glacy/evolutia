"""
Utilidades para parsear archivos Markdown/MyST y extraer ejercicios y soluciones.
"""
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for performance optimization
# Compiling regexes at module level avoids recompilation on every function call
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
EXERCISE_PATTERN = re.compile(r'(`{3,4})\{exercise\}(?:\s+\d+)?\s*\n:label:\s+(\S+)\s*\n(.*?)(?=\1)', re.DOTALL)
SOLUTION_PATTERN = re.compile(r'(`{3,4})\{solution\}\s+(\S+)\s*\n:label:\s+(\S+)\s*\n(.*?)(?=\1)', re.DOTALL)
INCLUDE_PATTERN = re.compile(r'```\{include\}\s+(.+?)\s*```', re.DOTALL)


def extract_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    """
    Extrae el frontmatter YAML del contenido Markdown.

    Args:
        content: Contenido completo del archivo

    Returns:
        Tupla (frontmatter_dict, contenido_sin_frontmatter)
    """
    if not content:
        return {}, ""

    match = FRONTMATTER_PATTERN.match(content)

    if match:
        frontmatter_str = match.group(1)
        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
            content_without_frontmatter = content[match.end():]
            logger.debug(f"[MarkdownParser] Frontmatter extraído: {len(frontmatter)} campos")
            return frontmatter, content_without_frontmatter
        except yaml.YAMLError as e:
            logger.warning(f"[MarkdownParser] Error parseando YAML frontmatter: {e}")
            return {}, content
    logger.debug("[MarkdownParser] No se encontró frontmatter")
    return {}, content


def extract_exercise_blocks(content: str) -> List[Dict[str, Union[str, None]]]:
    """
    Extrae bloques de ejercicio del formato MyST.

    Busca bloques del tipo:
    ```{exercise} N
    :label: exN-XX
    ...
    ```

    Args:
        content: Contenido Markdown

    Returns:
        Lista de diccionarios con información de cada ejercicio
    """
    exercises = []

    if not content:
        return exercises

    # Usa backreference \1 para coincidir con la longitud exacta del delimitador de cierre
    matches = EXERCISE_PATTERN.finditer(content)

    for match in matches:
        # group(1) es el delimitador
        label = match.group(2)
        exercise_content = match.group(3).strip()

        # Buscar si hay un include dentro
        include_match = INCLUDE_PATTERN.search(exercise_content)
        if include_match:
            include_path = include_match.group(1).strip()
            exercises.append({
                'label': label,
                'content': exercise_content,
                'include_path': include_path,
                'type': 'include'
            })
        else:
            exercises.append({
                'label': label,
                'content': exercise_content,
                'include_path': None,
                'type': 'inline'
            })

    logger.debug(f"[MarkdownParser] Extraídos {len(exercises)} bloques de ejercicio")
    return exercises


def extract_solution_blocks(content: str) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Extrae bloques de solución del formato MyST.

    Busca bloques del tipo:
    ````{solution} exN-XX
    :label: solution-exN-XX
    ...
    ````

    Args:
        content: Contenido Markdown

    Returns:
        Lista de diccionarios con información de cada solución
    """
    solutions = []

    if not content:
        return solutions

    matches = SOLUTION_PATTERN.finditer(content)

    for match in matches:
        # group(1) es delimitador
        exercise_label = match.group(2)
        solution_label = match.group(3)
        solution_content = match.group(4).strip()

        # Buscar includes dentro de la solución
        include_matches = INCLUDE_PATTERN.finditer(solution_content)
        include_paths = [m.group(1).strip() for m in include_matches]

        solutions.append({
            'exercise_label': exercise_label,
            'label': solution_label,
            'content': solution_content,
            'include_paths': include_paths
        })

    logger.debug(f"[MarkdownParser] Extraídos {len(solutions)} bloques de solución")
    return solutions


def read_markdown_file(file_path: Union[Path, str]) -> str:
    """
    Lee un archivo Markdown y retorna su contenido.

    Args:
        file_path: Ruta al archivo

    Returns:
        Contenido del archivo

    Raises:
        IOError: Si hay error leyendo el archivo
    """
    file_path = Path(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"[MarkdownParser] Archivo leído exitosamente: {file_path} (longitud={len(content)})")
            return content
    except Exception as e:
        logger.error(f"[MarkdownParser] Error leyendo archivo {file_path}: {e}")
        raise IOError(f"Error leyendo archivo {file_path}: {e}")


def resolve_include_path(include_path: str, base_dir: Union[Path, str]) -> Path:
    """
    Resuelve una ruta de include relativa a un directorio base.

    Args:
        include_path: Ruta relativa del include
        base_dir: Directorio base

    Returns:
        Ruta absoluta resuelta
    """
    # Limpiar la ruta (puede tener ./ o espacios)
    clean_path = include_path.strip().lstrip('./')
    resolved_path = (Path(base_dir) / clean_path).resolve()
    logger.debug(f"[MarkdownParser] Ruta include resuelta: {include_path} -> {resolved_path}")
    return resolved_path
