"""
Extractor de materiales didácticos.
Lee y parsea archivos Markdown de lecturas, prácticas y tareas.
"""

from pathlib import Path
from typing import Dict, List, Union
import logging
import time

try:
    from utils.markdown_parser import (
        read_markdown_file,
        extract_frontmatter,
        extract_exercise_blocks,
        extract_solution_blocks,
        resolve_include_path,
    )
except ImportError:
    from .utils.markdown_parser import (
        read_markdown_file,
        extract_frontmatter,
        extract_exercise_blocks,
        extract_solution_blocks,
        resolve_include_path,
    )


logger = logging.getLogger(__name__)


class MaterialExtractor:
    """Extrae ejercicios y soluciones de materiales didácticos."""

    def __init__(self, base_path: Union[Path, str]):
        """
        Inicializa el extractor.

        Args:
            base_path: Ruta base del proyecto (donde están los directorios de temas)
        """
        self.base_path = Path(base_path)
        self.exercises = []
        self.solutions = []
        # Caché de rutas de archivos válidos para evitar escaneos repetidos
        self._file_cache: Dict[Path, Dict] = {}
        # Timestamp del último escaneo
        self._last_scan_timestamp: float = 0
        # TTL del caché en segundos (5 minutos)
        self._cache_ttl = 300

    def extract_from_file(self, file_path: Path, use_cache: bool = True) -> Dict:
        """
        Extrae ejercicios y soluciones de un archivo Markdown.

        Args:
            file_path: Ruta al archivo
            use_cache: Si True, usa el caché si es válido (default: True)

        Returns:
            Diccionario con ejercicios y soluciones extraídos
        """
        # Verificar caché primero
        if use_cache and self._is_cache_valid(file_path):
            logger.debug(f"[MaterialExtractor] Usando caché para {file_path.name}")
            return self._file_cache[file_path]["data"]

        try:
            content = read_markdown_file(file_path)
            frontmatter, content_body = extract_frontmatter(content)

            exercises = extract_exercise_blocks(content_body)
            solutions = extract_solution_blocks(content_body)

            # Resolver includes de ejercicios
            for exercise in exercises:
                if exercise["include_path"]:
                    include_path = resolve_include_path(
                        exercise["include_path"], file_path.parent
                    )
                    if include_path.exists():
                        exercise["resolved_content"] = read_markdown_file(include_path)
                    else:
                        logger.warning(
                            f"[MaterialExtractor] Include no encontrado en ejercicio: {include_path} (archivo: {file_path})"
                        )
                        exercise["resolved_content"] = exercise["content"]
                else:
                    exercise["resolved_content"] = exercise["content"]

            # Resolver includes de soluciones
            for solution in solutions:
                resolved_content_parts = []
                for include_path_str in solution["include_paths"]:
                    include_path = resolve_include_path(
                        include_path_str, file_path.parent
                    )
                    if include_path.exists():
                        resolved_content_parts.append(read_markdown_file(include_path))
                    else:
                        logger.warning(
                            f"[MaterialExtractor] Include no encontrado en solución: {include_path} (archivo: {file_path})"
                        )

                if resolved_content_parts:
                    solution["resolved_content"] = "\n\n---\n\n".join(
                        resolved_content_parts
                    )
                else:
                    solution["resolved_content"] = solution["content"]

            result = {
                "file_path": file_path,
                "frontmatter": frontmatter,
                "exercises": exercises,
                "solutions": solutions,
                "content_body": content_body,  # Exponer contenido para indexación de lecturas
            }

            # Guardar en caché
            if use_cache:
                self._file_cache[file_path] = {
                    "data": result,
                    "timestamp": file_path.stat().st_mtime,
                }
                self._last_scan_timestamp = max(
                    self._last_scan_timestamp, file_path.stat().st_mtime
                )

            return result
        except Exception as e:
            logger.error(f"[MaterialExtractor] Error extrayendo de {file_path}: {e}")
            error_result = {
                "file_path": file_path,
                "frontmatter": {},
                "exercises": [],
                "solutions": [],
            }

            # Guardar incluso errores en caché para evitar reintentos fallidos
            if use_cache:
                self._file_cache[file_path] = {
                    "data": error_result,
                    "timestamp": time.time(),  # Usar tiempo actual para archivos que no existen
                }

            return error_result

    def extract_from_directory(
        self, directory: Path, pattern: str = "*.md"
    ) -> List[Dict]:
        """
        Extrae materiales de todos los archivos .md en un directorio.

        Args:
            directory: Directorio a procesar
            pattern: Patrón de búsqueda de archivos

        Returns:
            Lista de diccionarios con materiales extraídos
        """
        directory = Path(directory)
        if not directory.exists():
            logger.warning(f"[MaterialExtractor] Directorio no existe: {directory}")
            return []

        materials = []
        for md_file in directory.rglob(pattern):
            # Ignorar archivos en _build y otros directorios temporales
            if "_build" in md_file.parts or "node_modules" in md_file.parts:
                continue

            material = self.extract_from_file(md_file)
            # Incluirlos si tienen ejercicios/soluciones O si parecen ser materiales de lectura/teoría
            if (
                material["exercises"]
                or material["solutions"]
                or "lectura" in md_file.name.lower()
                or "teoria" in md_file.name.lower()
            ):
                materials.append(material)

        return materials

    def extract_by_topic(self, topic: str) -> List[Dict]:
        """
        Extrae materiales de un tema específico.

        Busca en:
        - {topic}/semana*_practica.md
        - {topic}/semana*_lectura.md
        - tareas/tarea*/tarea*.md

        Args:
            topic: Nombre del tema (ej: "analisis_vectorial")

        Returns:
            Lista de materiales extraídos
        """
        materials = []

        # Buscar en directorio del tema
        topic_dir = self.base_path / topic
        if topic_dir.exists():
            # Buscar prácticas
            practice_files = list(topic_dir.glob("*practica*.md"))
            for file in practice_files:
                materials.append(self.extract_from_file(file))

            # Buscar lecturas (pueden tener ejercicios)
            reading_files = list(topic_dir.glob("*lectura*.md"))
            for file in reading_files:
                materials.append(self.extract_from_file(file))

        # Buscar en tareas (pueden ser de múltiples temas)
        tareas_dir = self.base_path / "tareas"
        if tareas_dir.exists():
            for tarea_dir in tareas_dir.iterdir():
                if tarea_dir.is_dir():
                    tarea_file = tarea_dir / f"{tarea_dir.name}.md"
                    if tarea_file.exists():
                        material = self.extract_from_file(tarea_file)
                        # Filtrar por tema si es relevante (checking subject or tags)
                        subject_match = (
                            material["frontmatter"]
                            .get("subject", "")
                            .lower()
                            .find(topic.lower())
                            != -1
                        )
                        tags_match = any(
                            topic.lower() in tag.lower()
                            for tag in material["frontmatter"].get("tags", [])
                        )
                        if subject_match or tags_match:
                            materials.append(material)

        # Buscar en examenes (pueden ser de múltiples temas)
        examenes_dir = self.base_path / "examenes"
        if examenes_dir.exists():
            for examen_dir in examenes_dir.iterdir():
                if examen_dir.is_dir():
                    examen_file = examen_dir / f"{examen_dir.name}.md"
                    if examen_file.exists():
                        material = self.extract_from_file(examen_file)
                        # Filtrar por tema si es relevante
                        subject_match = (
                            material["frontmatter"]
                            .get("subject", "")
                            .lower()
                            .find(topic.lower())
                            != -1
                        )
                        tags_match = any(
                            topic.lower() in tag.lower()
                            for tag in material["frontmatter"].get("tags", [])
                        )

                        # Si es examen, a veces no tiene subject especifico o tiene "Examen X".
                        # Si no hay match explícito, tal vez incluirlo si no se encontraron otros materiales?
                        # Para seguridad, requerimos algún match en subject, tags o keywords
                        keywords_match = any(
                            topic.lower() in kw.lower()
                            for kw in material["frontmatter"].get("keywords", [])
                        )

                        if subject_match or tags_match or keywords_match:
                            materials.append(material)

        return materials

    def get_all_exercises(self, materials: List[Dict]) -> List[Dict]:
        """
        Obtiene todos los ejercicios de una lista de materiales.

        Args:
            materials: Lista de materiales extraídos

        Returns:
            Lista de ejercicios con sus metadatos
        """
        all_exercises = []

        for material in materials:
            # Pre-calcular el diccionario de soluciones para búsquedas O(1)
            solutions_by_label = {}
            for sol in material.get("solutions", []):
                if sol["exercise_label"] not in solutions_by_label:
                    solutions_by_label[sol["exercise_label"]] = sol

            for exercise in material["exercises"]:
                # Buscar solución correspondiente
                solution = solutions_by_label.get(exercise["label"])

                exercise_data = {
                    "label": exercise["label"],
                    "content": exercise["resolved_content"],
                    "source_file": material["file_path"],
                    "frontmatter": material["frontmatter"],
                    "solution": solution["resolved_content"] if solution else None,
                    "solution_label": solution["label"] if solution else None,
                }
                all_exercises.append(exercise_data)

        return all_exercises

    def clear_cache(self):
        """Limpia el caché de archivos."""
        self._file_cache.clear()
        self._last_scan_timestamp = 0
        logger.debug("[MaterialExtractor] Caché de archivos limpiado")

    def _is_cache_valid(self, file_path: Path) -> bool:
        """
        Verifica si el caché para un archivo es válido.

        Args:
            file_path: Ruta del archivo a verificar

        Returns:
            True si el caché es válido, False si necesita recacheo
        """
        if file_path not in self._file_cache:
            return False

        # Verificar si el archivo fue modificado
        try:
            _ = self._file_cache[file_path]
            file_mtime = file_path.stat().st_mtime

            # Usar el timestamp de escaneo más reciente para verificar
            if file_mtime > self._last_scan_timestamp:
                return False

            return True
        except (OSError, KeyError):
            return False

    def get_cache_stats(self) -> Dict:
        """
        Obtiene estadísticas del caché de archivos.

        Returns:
            Diccionario con estadísticas del caché
        """
        return {
            "cached_files": len(self._file_cache),
            "last_scan_timestamp": self._last_scan_timestamp,
            "cache_ttl": self._cache_ttl,
        }
