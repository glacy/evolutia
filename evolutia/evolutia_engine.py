"""
Motor principal de EvoluIA.
Encapsula la lógica de orquestación, extracción, análisis y generación paralela.
"""

import argparse
import asyncio
import logging
import random
import concurrent.futures
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
from tqdm import tqdm

# Imports from internal modules
from .material_extractor import MaterialExtractor
from .exercise_analyzer import ExerciseAnalyzer
from .variation_generator import VariationGenerator
from .complexity_validator import ComplexityValidator
from .exam_generator import ExamGenerator
from .config_manager import ConfigManager

# Conditional RAG imports
try:
    from .rag.rag_manager import RAGManager
    from .rag.enhanced_variation_generator import EnhancedVariationGenerator
    from .rag.consistency_validator import ConsistencyValidator

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)


class EvolutiaEngine:
    """
    Motor central que coordina el flujo de trabajo de EvolutIA.
    """

    def __init__(
        self,
        base_path: Union[Path, str],
        config_path: Optional[Union[Path, str]] = None,
    ):
        self.base_path = Path(base_path)
        self.config_path = Path(config_path) if config_path else None
        self.rag_manager = None

        # Load configuration manager
        self.config_manager = ConfigManager(base_path, config_path)
        self.full_config = self.config_manager.load_current_config()

    def initialize_rag(self, force_reindex: bool = False) -> bool:
        """
        Inicializa el subsistema RAG si está disponible.

        Returns:
            True si la inicialización fue exitosa
            False si no se pudo inicializar (RAG no disponible o error)
        """
        if not RAG_AVAILABLE:
            logger.error(
                "[EvolutiaEngine] RAG solicitado pero no disponible. Instala dependencias con: pip install -e '.[rag]'"
            )
            return False

        try:
            self.rag_manager = RAGManager(
                config_path=self.config_path, base_path=self.base_path
            )
            self.rag_manager.initialize(force_reindex=force_reindex)
            logger.info("[EvolutiaEngine] Subsistema RAG inicializado correctamente")
            return True
        except Exception as e:
            logger.error(
                f"[EvolutiaEngine] Error inicializando RAG (force_reindex={force_reindex}): {e}"
            )
            return False

    def get_api_config(self, provider: str) -> Dict[str, Any]:
        """Obtiene la configuración específica para una API."""
        return self.full_config.get("api", {}).get(provider, {})

    def extract_materials_and_exercises(
        self, topics: List[str], label_filter: Optional[List[str]] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Paso 1 & 2: Extrae materiales y lista todos los ejercicios disponibles.
        """
        logger.info("Paso 1: Extrayendo materiales didácticos...")
        extractor = MaterialExtractor(self.base_path)
        materials = []

        # 1. Extract by topic
        if topics:
            for topic in topics:
                topic_materials = extractor.extract_by_topic(topic)
                if topic_materials:
                    materials.extend(topic_materials)
                else:
                    logger.warning(
                        f"No se encontraron materiales para el tema: {topic}"
                    )

        # 2. Fallback: Search all if no materials found yet or topics were empty (e.g., list mode)
        if not materials:
            logger.info("Buscando en todos los directorios...")
            for topic_dir in self.base_path.iterdir():
                if topic_dir.is_dir() and topic_dir.name not in [
                    "_build",
                    "evolutia",
                    "proyecto",
                    ".git",
                ]:
                    materials.extend(extractor.extract_from_directory(topic_dir))

        if not materials:
            return [], []

        logger.info(f"Encontrados {len(materials)} archivos con materiales")

        # Get exercises
        logger.info("Paso 2: Obteniendo ejercicios...")
        all_exercises = extractor.get_all_exercises(materials)

        # Filter by label if requested
        if label_filter:
            logger.info(f"Filtrando por labels: {label_filter}")
            filtered = [ex for ex in all_exercises if ex.get("label") in label_filter]
            if not filtered:
                available = [ex.get("label") for ex in all_exercises if ex.get("label")]
                logger.warning(
                    f"No se encontraron ejercicios con los labels solicitados. Disponibles: {available[:10]}..."
                )
            all_exercises = filtered

        logger.info(f"Encontrados {len(all_exercises)} ejercicios")
        return materials, all_exercises

    def analyze_exercises(self, exercises: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Paso 3: Analiza la complejidad de los ejercicios."""
        logger.info("Paso 3: Analizando complejidad de ejercicios...")
        analyzer = ExerciseAnalyzer()
        exercises_with_analysis = []

        for exercise in exercises:
            analysis = analyzer.analyze(exercise)
            exercises_with_analysis.append((exercise, analysis))

        # Sort by total complexity descending
        exercises_with_analysis.sort(
            key=lambda x: x[1]["total_complexity"], reverse=True
        )
        return exercises_with_analysis

    def _generate_single_variation(
        self,
        generator: Union["VariationGenerator", "EnhancedVariationGenerator"],
        validator: Union["ComplexityValidator", "ConsistencyValidator"],
        exercise_base: Dict,
        analysis: Dict,
        args: argparse.Namespace,
    ) -> Optional[Dict]:
        """Helper para generar una única variación (thread-safe logic)."""
        attempt_count = 0
        while attempt_count < 3:
            try:
                # Generate
                if args.type == "multiple_choice":
                    variation = generator.generate_variation(
                        exercise_base,
                        analysis,
                        exercise_type=args.type,
                        max_tokens=args.max_tokens,
                    )
                elif not args.no_generar_soluciones:
                    variation = generator.generate_variation_with_solution(
                        exercise_base, analysis, max_tokens=args.max_tokens
                    )
                else:
                    variation = generator.generate_variation(
                        exercise_base,
                        analysis,
                        exercise_type=args.type,
                        max_tokens=args.max_tokens,
                    )

                if not variation:
                    attempt_count += 1
                    continue

                # Validate
                if args.use_rag:
                    validation = validator.validate(exercise_base, analysis, variation)
                    is_valid = validation["is_valid"]
                else:
                    validation = validator.validate(exercise_base, analysis, variation)
                    is_valid = validation["is_valid"]

                if is_valid:
                    return variation

            except Exception as e:
                logger.error(
                    f"[EvolutiaEngine] Error en hilo de generación (intento {attempt_count + 1}/3): {e}"
                )

            attempt_count += 1
        logger.debug(
            f"[EvolutiaEngine] Generación falló después de {attempt_count} intentos"
        )
        return None

    def _generate_creation_mode(
        self,
        generator: Union["VariationGenerator", "EnhancedVariationGenerator"],
        topic: str,
        tags: List[str],
        complexity: str,
        ex_type: str,
        args: argparse.Namespace,
    ) -> Optional[Dict]:
        """
        Helper para modo creación.

        Returns:
            Diccionario con el ejercicio generado o None si hubo error
        """
        try:
            logger.debug(
                f"[EvolutiaEngine] Creando nuevo ejercicio: topic={topic}, tags={tags}, complexity={complexity}"
            )
            return generator.generate_new_exercise_from_topic(
                topic,
                tags,
                difficulty=complexity,
                exercise_type=ex_type,
                max_tokens=args.max_tokens,
            )
        except Exception as e:
            logger.error(
                f"[EvolutiaEngine] Error en creación de ejercicio nuevo (topic={topic}): {e}"
            )
            return None

    def generate_variations_parallel(
        self,
        selected_exercises: List[Tuple[Dict, Dict]],
        args: argparse.Namespace,
        max_workers: int = 5,
    ) -> List[Dict]:
        """
        Paso 4: Genera variaciones en paralelo.
        """
        logger.info(
            f"Paso 4: Generando variaciones en paralelo (Workers: {max_workers})..."
        )

        # Setup Generator
        api_config = self.get_api_config(args.api)

        if (args.use_rag and self.rag_manager) or args.mode == "creation":
            retriever = (
                self.rag_manager.get_retriever()
                if (args.use_rag and self.rag_manager)
                else None
            )
            generator = EnhancedVariationGenerator(
                api_provider=args.api, retriever=retriever
            )
            validator = (
                ConsistencyValidator(retriever=retriever)
                if retriever
                else ComplexityValidator()
            )
        else:
            generator = VariationGenerator(api_provider=args.api)
            validator = ComplexityValidator()

        # Configure model
        if args.api == "local":
            generator.base_url = args.base_url or api_config.get(
                "base_url", "http://localhost:11434/v1"
            )
            generator.local_model = args.model or api_config.get("model", "llama3")
        elif args.api == "generic":
            generator.base_url = args.base_url or api_config.get("base_url")
            generator.model_name = args.model or api_config.get("model")
        elif args.api in ["openai", "anthropic", "deepseek", "gemini"]:
            if args.model:
                generator.model_name = args.model
            elif "model" in api_config:
                generator.model_name = api_config["model"]

        # Determine tasks based on mode
        tasks = []

        if args.mode == "creation":
            # Creation Mode Logic
            for i in range(args.num_ejercicios):
                current_topic = args.tema[i % len(args.tema)]
                current_tags = (
                    [args.tags[i % len(args.tags)]] if args.tags else [current_topic]
                )

                tasks.append(
                    {
                        "func": self._generate_creation_mode,
                        "args": (
                            generator,
                            current_topic,
                            current_tags,
                            args.complejidad,
                            args.type,
                            args,
                        ),
                    }
                )
        else:
            # Variation Mode Logic

            # If explicit lables, use exactly those
            if args.label:
                target_exercises = list(selected_exercises)
            else:
                # Random selection to fill num_ejercicios
                target_exercises = []
                candidates = selected_exercises[: max(5, len(selected_exercises) // 2)]
                for _ in range(args.num_ejercicios):
                    if candidates:
                        target_exercises.append(random.choice(candidates))

            for ex_base, analysis in target_exercises:
                tasks.append(
                    {
                        "func": self._generate_single_variation,
                        "args": (generator, validator, ex_base, analysis, args),
                    }
                )

        # Execute Parallel
        valid_variations = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {}
            for t in tasks:
                future = executor.submit(t["func"], *t["args"])
                future_to_task[future] = t
                # Stagger requests to avoid hitting rate limits instantly
                time.sleep(1.0)

            for future in tqdm(
                concurrent.futures.as_completed(future_to_task),
                total=len(tasks),
                desc="Generando",
            ):
                try:
                    result = future.result()
                    if result:
                        valid_variations.append(result)
                except Exception as e:
                    logger.error(f"Excepción no manejada en worker: {e}")

        logger.info(
            f"Generación completada. {len(valid_variations)} variaciones exitosas."
        )
        return valid_variations

    async def _generate_single_variation_async(
        self,
        generator: Union["VariationGenerator", "EnhancedVariationGenerator"],
        validator: Union["ComplexityValidator", "ConsistencyValidator"],
        exercise_base: Dict,
        analysis: Dict,
        args: argparse.Namespace,
        semaphore: asyncio.Semaphore,
    ) -> Optional[Dict]:
        """
        Helper asíncrono para generar una única variación.

        Args:
            generator: Generador de variaciones
            validator: Validador de complejidad
            exercise_base: Ejercicio base
            analysis: Análisis del ejercicio
            args: Argumentos CLI
            semaphore: Semaphore para limitar concurrencia

        Returns:
            Variación generada o None
        """
        async with semaphore:
            attempt_count = 0
            while attempt_count < 3:
                try:
                    # Ejecutar generación sincrónica en un thread
                    loop = asyncio.get_event_loop()
                    if args.type == "multiple_choice":
                        variation = await loop.run_in_executor(
                            None,
                            generator.generate_variation,
                            exercise_base,
                            analysis,
                            exercise_type=args.type,
                            max_tokens=args.max_tokens,
                        )
                    elif not args.no_generar_soluciones:
                        variation = await loop.run_in_executor(
                            None,
                            generator.generate_variation_with_solution,
                            exercise_base,
                            analysis,
                            max_tokens=args.max_tokens,
                        )
                    else:
                        variation = await loop.run_in_executor(
                            None,
                            generator.generate_variation,
                            exercise_base,
                            analysis,
                            exercise_type=args.type,
                            max_tokens=args.max_tokens,
                        )

                    if not variation:
                        attempt_count += 1
                        continue

                    # Validar
                    validation = await loop.run_in_executor(
                        None, validator.validate, exercise_base, analysis, variation
                    )
                    is_valid = validation["is_valid"]

                    if is_valid:
                        return variation

                except Exception as e:
                    logger.error(
                        f"[EvolutiaEngine] Error en async worker (intento {attempt_count + 1}/3): {e}"
                    )

                attempt_count += 1
            logger.debug(
                f"[EvolutiaEngine] Generación async falló después de {attempt_count} intentos"
            )
            return None

    async def _generate_creation_mode_async(
        self,
        generator: Union["VariationGenerator", "EnhancedVariationGenerator"],
        topic: str,
        tags: List[str],
        complexity: str,
        ex_type: str,
        args: argparse.Namespace,
        semaphore: asyncio.Semaphore,
    ) -> Optional[Dict]:
        """
        Helper asíncrono para modo creación.

        Returns:
            Diccionario con el ejercicio generado o None si hubo error
        """
        async with semaphore:
            try:
                logger.debug(
                    f"[EvolutiaEngine] Creando nuevo ejercicio async: topic={topic}, tags={tags}"
                )
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    generator.generate_new_exercise_from_topic,
                    topic,
                    tags,
                    complexity,
                    ex_type,
                    args.max_tokens,
                )
            except Exception as e:
                logger.error(
                    f"[EvolutiaEngine] Error en async creación (topic={topic}): {e}"
                )
                return None

    def generate_variations_async(
        self,
        selected_exercises: List[Tuple[Dict, Dict]],
        args: argparse.Namespace,
        max_workers: int = 5,
    ) -> List[Dict]:
        """
        Generación de variaciones usando asyncio (async/await).

        Más eficiente que ThreadPoolExecutor para operaciones I/O-bound como llamadas a LLM APIs.

        Args:
            selected_exercises: Lista de ejercicios seleccionados con análisis
            args: Argumentos CLI
            max_workers: Número máximo de workers concurrentes

        Returns:
            Lista de variaciones generadas exitosamente
        """
        logger.info(
            f"Paso 4: Generando variaciones con asyncio (max_workers={max_workers})..."
        )

        # Setup Generator
        api_config = self.get_api_config(args.api)

        if (args.use_rag and self.rag_manager) or args.mode == "creation":
            retriever = (
                self.rag_manager.get_retriever()
                if (args.use_rag and self.rag_manager)
                else None
            )
            generator = EnhancedVariationGenerator(
                api_provider=args.api, retriever=retriever
            )
            validator = (
                ConsistencyValidator(retriever=retriever)
                if retriever
                else ComplexityValidator()
            )
        else:
            generator = VariationGenerator(api_provider=args.api)
            validator = ComplexityValidator()

        # Configure model
        if args.api == "local":
            generator.base_url = args.base_url or api_config.get(
                "base_url", "http://localhost:11434/v1"
            )
            generator.local_model = args.model or api_config.get("model", "llama3")
        elif args.api == "generic":
            generator.base_url = args.base_url or api_config.get("base_url")
            generator.model_name = args.model or api_config.get("model")
        elif args.api in ["openai", "anthropic", "deepseek", "gemini"]:
            if args.model:
                generator.model_name = args.model
            elif "model" in api_config:
                generator.model_name = api_config["model"]

        # Determine tasks
        tasks = []

        if args.mode == "creation":
            for i in range(args.num_ejercicios):
                current_topic = args.tema[i % len(args.tema)]
                current_tags = (
                    [args.tags[i % len(args.tags)]] if args.tags else [current_topic]
                )
                tasks.append(
                    (
                        "creation",
                        generator,
                        current_topic,
                        current_tags,
                        args.complejidad,
                        args.type,
                        args.max_tokens,
                    )
                )
        else:
            if args.label:
                target_exercises = list(selected_exercises)
            else:
                target_exercises = []
                candidates = selected_exercises[: max(5, len(selected_exercises) // 2)]
                for _ in range(args.num_ejercicios):
                    if candidates:
                        target_exercises.append(random.choice(candidates))

            for ex_base, analysis in target_exercises:
                tasks.append(
                    ("variation", generator, validator, ex_base, analysis, args)
                )

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_workers)

        # Create async tasks
        async_tasks = []
        for task_info in tasks:
            if task_info[0] == "creation":
                async_tasks.append(
                    self._generate_creation_mode_async(
                        task_info[1],  # generator
                        task_info[2],  # topic
                        task_info[3],  # tags
                        task_info[4],  # complexity
                        task_info[5],  # ex_type
                        task_info[6],  # max_tokens
                        semaphore,
                    )
                )
            else:
                async_tasks.append(
                    self._generate_single_variation_async(
                        task_info[1],  # generator
                        task_info[2],  # validator
                        task_info[3],  # ex_base
                        task_info[4],  # analysis
                        task_info[5],  # args
                        semaphore,
                    )
                )

        # Execute all tasks concurrently
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # ⚡ Bolt Optimization:
        # Wrap the iteration in an async function and call run_until_complete() ONCE.
        # This fixes an anti-pattern where loop.run_until_complete() was called inside a for loop,
        # repeatedly starting and stopping the event loop and adding unnecessary overhead.
        # Performance Impact: Removes event loop startup/teardown overhead per iteration.
        async def run_all():
            results = []
            for coro in tqdm(
                asyncio.as_completed(async_tasks),
                total=len(async_tasks),
                desc="Generando",
            ):
                try:
                    result = await coro
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Excepción no manejada en async worker: {e}")
            return results

        valid_variations = loop.run_until_complete(run_all())

        logger.info(
            f"Generación async completada. {len(valid_variations)} variaciones exitosas."
        )
        return valid_variations

    def generate_exam_files(
        self,
        variations: List[Dict],
        args: argparse.Namespace,
        output_dir: Union[Path, str],
        exam_number: int,
    ) -> bool:
        """Paso 5: Genera los archivos finales del examen."""
        logger.info("Paso 5: Generando archivos de examen...")
        exam_gen = ExamGenerator(self.base_path)

        keywords = args.keywords or []
        metadata = {
            "model": args.api,  # Simplified, internal details hidden
            "provider": args.api,
            "rag_enabled": args.use_rag,
            "mode": args.mode,
            "target_difficulty": args.complejidad,
        }

        return exam_gen.generate_exam(
            variations,
            exam_number,
            output_dir,
            args.subject,
            keywords,
            metadata=metadata,
        )
