"""
Utilidades para parsear archivos Markdown/MyST y extraer ejercicios y soluciones.
"""
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def extract_frontmatter(content: str) -> Tuple[Dict, str]:
    """
    Extrae el frontmatter YAML del contenido Markdown.
    
    Args:
        content: Contenido completo del archivo
        
    Returns:
        Tupla (frontmatter_dict, contenido_sin_frontmatter)
    """
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if match:
        frontmatter_str = match.group(1)
        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
            content_without_frontmatter = content[match.end():]
            return frontmatter, content_without_frontmatter
        except yaml.YAMLError:
            return {}, content
    return {}, content


def extract_exercise_blocks(content: str) -> List[Dict]:
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
    
    # Patrón para bloques de ejercicio MyST
    # Puede ser ```{exercise} o ````{exercise}
    exercise_pattern = r'`{3,4}\{exercise\}(?:\s+\d+)?\s*\n:label:\s+(\S+)\s*\n(.*?)(?=`{3,4})'
    
    matches = re.finditer(exercise_pattern, content, re.DOTALL)
    
    for match in matches:
        label = match.group(1)
        exercise_content = match.group(2).strip()
        
        # Buscar si hay un include dentro
        include_match = re.search(r'```\{include\}\s+(.+?)\s*```', exercise_content, re.DOTALL)
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
    
    return exercises


def extract_solution_blocks(content: str) -> List[Dict]:
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
    
    # Patrón para bloques de solución MyST
    solution_pattern = r'`{3,4}\{solution\}\s+(\S+)\s*\n:label:\s+(\S+)\s*\n(.*?)(?=`{3,4})'
    
    matches = re.finditer(solution_pattern, content, re.DOTALL)
    
    for match in matches:
        exercise_label = match.group(1)
        solution_label = match.group(2)
        solution_content = match.group(3).strip()
        
        # Buscar includes dentro de la solución
        include_matches = re.finditer(r'```\{include\}\s+(.+?)\s*```', solution_content, re.DOTALL)
        include_paths = [m.group(1).strip() for m in include_matches]
        
        solutions.append({
            'exercise_label': exercise_label,
            'label': solution_label,
            'content': solution_content,
            'include_paths': include_paths
        })
    
    return solutions


def read_markdown_file(file_path: Path) -> str:
    """
    Lee un archivo Markdown y retorna su contenido.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        Contenido del archivo
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error leyendo archivo {file_path}: {e}")


def resolve_include_path(include_path: str, base_dir: Path) -> Path:
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
    return (base_dir / clean_path).resolve()

