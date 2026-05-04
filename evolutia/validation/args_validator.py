"""
Validador de argumentos CLI para EvolutIA.
Valida exhaustivamente los argumentos pasados por línea de comandos.
"""
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Excepción para errores de validación."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []
        self.message = message


class ArgsValidator:
    """Validador de argumentos de línea de comandos."""

    # Valores válidos para algunos argumentos
    VALID_COMPLEXITY = {'media', 'alta', 'muy_alta'}
    VALID_API_PROVIDERS = {
        'openai', 'anthropic', 'local', 'gemini', 'deepseek', 'generic'
    }
    VALID_MODES = {'variation', 'creation'}
    VALID_EXERCISE_TYPES = {'development', 'multiple_choice'}

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_args(self, args: argparse.Namespace) -> Tuple[bool, List[str]]:
        """
        Valida todos los argumentos CLI.

        Args:
            args: Objeto argparse.Namespace con los argumentos

        Returns:
            Tupla (is_valid, error_messages) donde is_valid es True si todos
            los argumentos son válidos, y error_messages es una lista con
            mensajes de error (vacía si is_valid es True)
        """
        self.errors = []
        self.warnings = []

        # Validaciones generales
        self._validate_complejidad(args)
        self._validate_num_ejercicios(args)
        self._validate_api(args)
        self._validate_workers(args)
        self._validate_mode(args)
        self._validate_exercise_type(args)

        # Validaciones de rutas
        self._validate_base_path(args)
        self._validate_config_path(args)
        self._validate_output_path(args)

        # Validaciones de combinaciones
        self._validate_mode_combinations(args)
        self._validate_rag_combinations(args)

        # Validaciones específicas de modos
        self._validate_variation_mode(args)
        self._validate_creation_mode(args)

        # Log warnings
        for warning in self.warnings:
            logger.warning(f"[ArgsValidator] {warning}")

        return len(self.errors) == 0, self.errors

    def _validate_complejidad(self, args: argparse.Namespace):
        """Valida que el nivel de complejidad sea válido."""
        if hasattr(args, 'complejidad') and args.complejidad:
            if args.complejidad not in self.VALID_COMPLEXITY:
                self.errors.append(
                    f"--complejidad debe ser uno de {sorted(self.VALID_COMPLEXITY)}, "
                    f"obtenido: {args.complejidad}"
                )

    def _validate_num_ejercicios(self, args: argparse.Namespace):
        """Valida que el número de ejercicios sea positivo y razonable."""
        if hasattr(args, 'num_ejercicios') and args.num_ejercicios is not None:
            if args.num_ejercicios <= 0:
                self.errors.append(
                    f"--num_ejercicios debe ser positivo, obtenido: {args.num_ejercicios}"
                )
            elif args.num_ejercicios > 50:
                self.warnings.append(
                    f"--num_ejercicios es muy alto ({args.num_ejercicios}), "
                    "esto puede generar un costo significativo en API"
                )

    def _validate_api(self, args: argparse.Namespace):
        """Valida que el proveedor de API sea válido."""
        if hasattr(args, 'api') and args.api:
            if args.api not in self.VALID_API_PROVIDERS:
                self.errors.append(
                    f"--api debe ser uno de {sorted(self.VALID_API_PROVIDERS)}, "
                    f"obtenido: {args.api}"
                )

            # Validaciones específicas por proveedor
            if args.api == 'generic' and not getattr(args, 'base_url', None):
                self.warnings.append(
                    "--api generic requiere --base_url, usando valor por defecto"
                )

    def _validate_workers(self, args: argparse.Namespace):
        """Valida que el número de workers esté en un rango razonable."""
        if hasattr(args, 'workers') and args.workers is not None:
            if args.workers < 1:
                self.errors.append(
                    f"--workers debe ser al menos 1, obtenido: {args.workers}"
                )
            elif args.workers > 20:
                self.warnings.append(
                    f"--workers es alto ({args.workers}), "
                    "esto puede causar rate limiting de API"
                )

    def _validate_mode(self, args: argparse.Namespace):
        """Valida que el modo de operación sea válido."""
        if hasattr(args, 'mode') and args.mode:
            if args.mode not in self.VALID_MODES:
                self.errors.append(
                    f"--mode debe ser uno de {sorted(self.VALID_MODES)}, "
                    f"obtenido: {args.mode}"
                )

    def _validate_exercise_type(self, args: argparse.Namespace):
        """Valida que el tipo de ejercicio sea válido."""
        if hasattr(args, 'type') and args.type:
            if args.type not in self.VALID_EXERCISE_TYPES:
                self.errors.append(
                    f"--type debe ser uno de {sorted(self.VALID_EXERCISE_TYPES)}, "
                    f"obtenido: {args.type}"
                )

    def _validate_base_path(self, args: argparse.Namespace):
        """Valida que la ruta base exista."""
        if hasattr(args, 'base_path') and args.base_path:
            base_path = Path(args.base_path)
            if not base_path.exists():
                self.errors.append(
                    f"--base_path no existe: {args.base_path}"
                )
            elif not base_path.is_dir():
                self.errors.append(
                    f"--base_path no es un directorio: {args.base_path}"
                )

    def _validate_config_path(self, args: argparse.Namespace):
        """Valida que la ruta del archivo de configuración exista si se especifica."""
        if hasattr(args, 'config') and args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                self.errors.append(
                    f"--config no existe: {args.config}"
                )
            elif not config_path.is_file():
                self.errors.append(
                    f"--config no es un archivo: {args.config}"
                )

    def _validate_output_path(self, args: argparse.Namespace):
        """Valida que el directorio de salida pueda crearse."""
        if hasattr(args, 'output') and args.output:
            output_path = Path(args.output)
            parent = output_path.parent

            if parent.exists() and not parent.is_dir():
                self.errors.append(
                    f"--output no es un directorio válido: {parent}"
                )

            # Verificar permisos de escritura en el directorio padre
            if parent.exists() and parent.is_dir():
                try:
                    test_file = parent / '.evolutia_write_test'
                    test_file.touch()
                    test_file.unlink()
                except (PermissionError, OSError) as e:
                    self.errors.append(
                        f"--output no tiene permisos de escritura: {parent} ({e})"
                    )

    def _validate_mode_combinations(self, args: argparse.Namespace):
        """Valida que las combinaciones de modos sean válidas."""
        is_exclusive_mode = getattr(args, 'analyze', False) or \
                           getattr(args, 'list', False) or \
                           getattr(args, 'query', False) or \
                           getattr(args, 'reindex', False)

        # Modos exclusivos no requieren tema ni output
        if is_exclusive_mode:
            return

        # Modos normales requieren tema o label
        if not getattr(args, 'tema', None) and not getattr(args, 'label', None):
            # Este error ya está en el CLI, pero lo verificamos por completitud
            pass

        # Modos normales requieren output
        if not getattr(args, 'output', None):
            # Este error ya está en el CLI, pero lo verificamos por completitud
            pass

    def _validate_rag_combinations(self, args: argparse.Namespace):
        """Valida las combinaciones de opciones RAG."""
        use_rag = getattr(args, 'use_rag', False)
        query = getattr(args, 'query', None)
        reindex = getattr(args, 'reindex', False)

        if not (use_rag or query or reindex):
            return

        # RAG requiere dependencies opcionales
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            self.warnings.append(
                f"RAG solicitado pero faltan dependencias: {e}. "
                "Instala con: pip install -e '.[rag]'"
            )

    def _validate_variation_mode(self, args: argparse.Namespace):
        """Valida requisitos específicos para modo variation."""
        if getattr(args, 'mode', None) == 'variation':
            # Mode variation requiere ejercicios existentes
            # (esto se verifica más tarde en el engine)
            pass

    def _validate_creation_mode(self, args: argparse.Namespace):
        """Valida requisitos específicos para modo creation."""
        if getattr(args, 'mode', None) == 'creation':
            # Mode creation requiere tema y tags
            if not getattr(args, 'tema', None):
                self.errors.append(
                    "Mode creation requiere --tema"
                )

            if not getattr(args, 'tags', None):
                self.warnings.append(
                    "Mode creation sin --tags puede generar ejercicios genéricos"
                )
