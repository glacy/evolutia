#!/usr/bin/env python3
"""
Script principal para generar exámenes a partir de materiales didácticos.
"""
import argparse
import logging
import sys
from pathlib import Path
from tqdm import tqdm

# Agregar el directorio actual al path para imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Imports absolutos para ejecución directa
try:
    from material_extractor import MaterialExtractor
    from exercise_analyzer import ExerciseAnalyzer
    from variation_generator import VariationGenerator
    from complexity_validator import ComplexityValidator
    from exam_generator import ExamGenerator
except ImportError:
    # Fallback a imports relativos si se importa como módulo
    from .material_extractor import MaterialExtractor
    from .exercise_analyzer import ExerciseAnalyzer
    from .variation_generator import VariationGenerator
    from .complexity_validator import ComplexityValidator
    from .exam_generator import ExamGenerator

# Imports condicionales para RAG
if True:  # Siempre intentar importar, fallar gracefully si no está disponible
    try:
        from rag.rag_manager import RAGManager
        from rag.enhanced_variation_generator import EnhancedVariationGenerator
        from rag.consistency_validator import ConsistencyValidator
        RAG_AVAILABLE = True
    except ImportError:
        try:
            from .rag.rag_manager import RAGManager
            from .rag.enhanced_variation_generator import EnhancedVariationGenerator
            from .rag.consistency_validator import ConsistencyValidator
            RAG_AVAILABLE = True
        except ImportError:
            RAG_AVAILABLE = False
            logger.warning("RAG no disponible. Instala dependencias: pip install chromadb sentence-transformers")


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Genera preguntas de examen basadas en materiales didácticos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Generar examen de análisis vectorial con 4 ejercicios
  python evolutia.py --tema analisis_vectorial --num_ejercicios 4 --output examenes/examen3
  
  # Generar examen con complejidad alta usando Claude
  python evolutia.py --tema matrices --num_ejercicios 3 --complejidad alta --api anthropic
        """
    )
    
    parser.add_argument(
        '--tema',
        type=str,
        required=False,
        nargs='+',
        help='Temas del examen (ej: analisis_vectorial matrices edps) [Requerido excepto para --reindex]'
    )
    
    parser.add_argument(
        '--num_ejercicios',
        type=int,
        default=4,
        help='Número de ejercicios a generar (default: 4)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        required=False,
        help='Directorio de salida para los archivos del examen [Requerido excepto para --reindex]'
    )
    
    parser.add_argument(
        '--complejidad',
        type=str,
        choices=['media', 'alta', 'muy_alta'],
        default='alta',
        help='Nivel de complejidad objetivo (default: alta)'
    )
    
    parser.add_argument(
        '--api',
        type=str,
        choices=['openai', 'anthropic', 'local', 'gemini'],
        default='openai',
        help='Proveedor de API de IA (default: openai)'
    )
    
    parser.add_argument(
        '--base_path',
        type=str,
        default='.',
        help='Ruta base del proyecto (default: directorio actual)'
    )
    
    parser.add_argument(
        '--examen_num',
        type=int,
        help='Número del examen (si no se especifica, se infiere del directorio)'
    )
    
    parser.add_argument(
        '--no_generar_soluciones',
        action='store_true',
        help='NO generar las soluciones de los ejercicios (por defecto siempre se generan)'
    )
    
    parser.add_argument(
        '--subject',
        type=str,
        default='IF3602 - II semestre 2025',
        help='Asignatura del examen'
    )
    
    parser.add_argument(
        '--keywords',
        type=str,
        nargs='+',
        help='Palabras clave para el examen'
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['variation', 'creation'],
        default='variation',
        help='Modo de operación: variacion (default) o creacion (desde cero)'
    )

    parser.add_argument(
        '--tags',
        type=str,
        nargs='+',
        help='Tags específicos para generación en modo creacion'
    )
    
    parser.add_argument(
        '--use_rag',
        action='store_true',
        help='Usar RAG para enriquecer generación con contexto del curso'
    )
    
    parser.add_argument(
        '--reindex',
        action='store_true',
        help='Forzar re-indexación de materiales (solo con --use_rag)'
    )
    
    args = parser.parse_args()
    
    # Validar argumentos requeridos dependiendo del modo
    if not args.reindex:
        if not args.tema:
            parser.error("el argumento --tema es requerido (a menos que se use --reindex)")
        if not args.output:
            parser.error("el argumento --output es requerido (a menos que se use --reindex)")
    
    # Validar argumentos
    base_path = Path(args.base_path).resolve()
    if not base_path.exists():
        logger.error(f"Ruta base no existe: {base_path}")
        return 1
    
    output_dir = None
    exam_number = 1
    
    if args.output:
        output_dir = Path(args.output).resolve()
        
        # Determinar número de examen
        if args.examen_num:
            exam_number = args.examen_num
        else:
            # Intentar inferir del nombre del directorio
            dir_name = output_dir.name
            if 'examen' in dir_name.lower():
                try:
                    exam_number = int(''.join(filter(str.isdigit, dir_name)))
                except ValueError:
                    exam_number = 1
            else:
                exam_number = 1
    
    logger.info(f"Iniciando generación de examen {exam_number}")
    logger.info(f"Tema: {args.tema}")
    logger.info(f"Número de ejercicios: {args.num_ejercicios}")
    logger.info(f"Directorio de salida: {output_dir}")
    logger.info(f"API: {args.api}")
    logger.info(f"RAG: {'Habilitado' if args.use_rag else 'Deshabilitado'}")
    
    # Inicializar RAG si está habilitado
    rag_manager = None
    if args.use_rag:
        if not RAG_AVAILABLE:
            logger.error("RAG solicitado pero no disponible. Instala: pip install chromadb sentence-transformers")
            return 1
        
        try:
            config_path = base_path / 'evolutia' / 'config' / 'config.yaml'
            rag_manager = RAGManager(config_path=config_path, base_path=base_path)
            rag_manager.initialize(force_reindex=args.reindex)
            logger.info("Sistema RAG inicializado")
            
            # Si solo se solicitó reindexar (y no hay tema/output), terminar aquí
            if args.reindex and not (args.tema and args.output):
                logger.info("Reindexado completado exitosamente.")
                return 0
                
        except Exception as e:
            logger.error(f"Error inicializando RAG: {e}")
            if args.use_rag:
                logger.error("No se puede continuar sin RAG. Usa --use_rag solo si RAG está configurado.")
                return 1
    
    try:
        # 1. Extraer materiales
        logger.info("Paso 1: Extrayendo materiales didácticos...")
        extractor = MaterialExtractor(base_path)
        materials = []
        topics = args.tema if isinstance(args.tema, list) else [args.tema]

        for topic in topics:
            topic_materials = extractor.extract_by_topic(topic)
            if topic_materials:
                materials.extend(topic_materials)
            else:
                logger.warning(f"No se encontraron materiales para el tema: {topic}")
        
        if not materials:
            logger.warning(f"No se encontraron materiales para los temas solicitados: {args.tema}")
            logger.info("Buscando en todos los directorios...")
            # Buscar en todos los temas
            for topic_dir in base_path.iterdir():
                if topic_dir.is_dir() and topic_dir.name not in ['_build', 'generador_examenes', 'examenes', 'tareas', 'proyecto']:
                    materials.extend(extractor.extract_from_directory(topic_dir))
        
        if not materials:
            logger.error("No se encontraron materiales didácticos")
            return 1
        
        logger.info(f"Encontrados {len(materials)} archivos con materiales")
        
        # 2. Obtener todos los ejercicios
        logger.info("Paso 2: Obteniendo ejercicios...")
        all_exercises = extractor.get_all_exercises(materials)
        
        if not all_exercises:
            logger.error("No se encontraron ejercicios en los materiales")
            return 1
        
        logger.info(f"Encontrados {len(all_exercises)} ejercicios")
        
        # 3. Analizar ejercicios
        logger.info("Paso 3: Analizando complejidad de ejercicios...")
        analyzer = ExerciseAnalyzer()
        exercises_with_analysis = []
        
        for exercise in all_exercises:
            analysis = analyzer.analyze(exercise)
            exercises_with_analysis.append((exercise, analysis))
        
        # 3.5. Indexar materiales si RAG está habilitado y no está indexado
        if args.use_rag and rag_manager:
            if not rag_manager.is_indexed() or args.reindex:
                logger.info("Indexando materiales en RAG...")
                rag_manager.index_materials(materials, analyzer, clear_existing=args.reindex)
                logger.info("Indexación completada")
            else:
                logger.info("RAG ya está indexado, usando índice existente")
        
        # Ordenar por complejidad (mayor primero para seleccionar los más complejos como base)
        # Si RAG está habilitado, podríamos usar búsqueda semántica para seleccionar
        exercises_with_analysis.sort(key=lambda x: x[1]['total_complexity'], reverse=True)
        
        # Seleccionar ejercicios base
        selected_exercises = exercises_with_analysis[:args.num_ejercicios * 2]  # Tomar más para tener opciones
        
        logger.info(f"Seleccionados {len(selected_exercises)} ejercicios candidatos")
        
        # 4. Generar variaciones
        logger.info("Paso 4: Generando variaciones con mayor complejidad...")
        
        # Cargar configuración de API
        config_path = base_path / 'evolutia' / 'config' / 'config.yaml'
        import yaml
        api_config = {}
        if config_path.exists():
            try:
                full_config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
                api_config = full_config.get('api', {}).get(args.api, {})
            except Exception as e:
                logger.warning(f"No se pudo cargar config: {e}")

        # Inicializar generador
        # Inicializar generador
        generator = None
        if (args.use_rag and rag_manager) or args.mode == 'creation':
            retriever = rag_manager.get_retriever() if (args.use_rag and rag_manager) else None
            generator = EnhancedVariationGenerator(
                api_provider=args.api,
                retriever=retriever
            )
            validator = ConsistencyValidator(retriever=retriever) if retriever else ComplexityValidator()
        else:
            generator = VariationGenerator(api_provider=args.api)
            validator = ComplexityValidator()
            
        # Configurar modelo y parámetros según proveedor
        if args.api == 'local':
            generator.base_url = api_config.get('base_url', "http://localhost:11434/v1")
            generator.local_model = api_config.get('model', "llama3")
            logger.info(f"Usando LLM local: {generator.local_model} en {generator.base_url}")
        elif args.api in ['openai', 'anthropic']:
            if 'model' in api_config:
                generator.model_name = api_config['model']
                logger.info(f"Usando modelo configurado: {generator.model_name}")

        valid_variations = []
        
        # MODO CREACIÓN: Generar desde cero
        if args.mode == 'creation':
            logger.info(f"MODO CREACIÓN: Generando {args.num_ejercicios} ejercicios nuevos para: {args.tema}")
            
            # if not isinstance(generator, EnhancedVariationGenerator):
            #    logger.error("El modo creación REQUIERE usar RAG (--use_rag).")
            #    return 1
                
            for i in tqdm(range(args.num_ejercicios), desc="Creando ejercicios"):
                # Estrategia Round-Robin para temas y tags
                # Si se dan múltiples, se rotan para distribuir la generación
                
                # Seleccionar tema actual
                current_topic = args.tema[i % len(args.tema)]
                
                # Seleccionar tags actuales
                if args.tags:
                    # Si hay tags explícitos, usamos uno por vez rotando
                    current_tags = [args.tags[i % len(args.tags)]]
                else:
                    # Si no hay tags, usamos el tema como tag
                    current_tags = [current_topic]
                
                # Intentar variar un poco los tags si es posible para tener diversidad
                # Por ahora usamos los mismos
                
                variation = generator.generate_new_exercise_from_topic(current_topic, current_tags, difficulty=args.complejidad)
                
                if variation:
                    valid_variations.append(variation)
                else:
                    logger.warning(f"Fallo al crear ejercicio {i+1}")
                    
        # MODO VARIACIÓN: Usar ejercicios existentes (Flujo original)
        else:
            valid_variations = []
            attempts = 0
            max_attempts = args.num_ejercicios * 3  # Intentar hasta 3 veces por ejercicio
            
            # Usar selected_exercises que viene de pasos anteriores
            # ... (código original de selección y bucle while)
            
            import random
            while len(valid_variations) < args.num_ejercicios and attempts < max_attempts:
                # Seleccionar ejercicio base
                # Preferir los de mayor complejidad, pero con algo de aleatoriedad
                ejercicio_base, analysis = random.choice(selected_exercises[:max(5, len(selected_exercises)//2)])
                
                try:
                    # Generar variación
                    variation = generator.generate_variation(ejercicio_base, analysis)
                    
                    if variation:
                        # Validar si es realmente más compleja (o consistente en caso de RAG)
                        is_valid = False
                        if args.use_rag:
                             # En RAG validamos consistencia y estilo
                             validation = validator.validate(variation, ejercicio_base)
                             is_valid = validation['is_consistent']
                        else:
                            # Validación clásica de complejidad
                            var_analysis = analyzer.analyze({
                                'content': variation['variation_content'], 
                                'solution': variation['variation_solution']
                            })
                            validation = validator.validate(var_analysis, analysis)
                            is_valid = validation['is_more_complex']
                        
                        if is_valid:
                            valid_variations.append(variation)
                            logger.info(f"Variación generada exitosamente ({len(valid_variations)}/{args.num_ejercicios})")
                        else:
                            logger.info("Variación rechazada por validación")
                except Exception as e:
                    logger.error(f"Error generando variación: {e}")
                
                attempts += 1
        


        
        if len(valid_variations) < args.num_ejercicios:
            logger.warning(
                f"Solo se generaron {len(valid_variations)} variaciones válidas "
                f"de {args.num_ejercicios} solicitadas"
            )
        
        if not valid_variations:
            logger.error("No se generaron variaciones válidas")
            return 1
        
        # 5. Generar archivos de examen
        logger.info("Paso 5: Generando archivos de examen...")
        exam_gen = ExamGenerator(base_path)
        
        keywords = args.keywords or []
        # Preparar metadatos para los archivos generados
        metadata = {
            'model': getattr(generator, 'local_model', None) or getattr(generator, 'model_name', None) or args.api,
            'provider': args.api,
            'rag_enabled': args.use_rag
        }
        
        success = exam_gen.generate_exam(
            valid_variations,
            exam_number,
            output_dir,
            args.subject,
            keywords,
            metadata=metadata
        )
        
        if success:
            logger.info(f"✓ Examen generado exitosamente en: {output_dir}")
            logger.info(f"  - Archivo principal: examen{exam_number}.md")
            logger.info(f"  - {len(valid_variations)} ejercicios generados")
            return 0
        else:
            logger.error("Error generando archivos de examen")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
        return 1
    except Exception as e:
        logger.exception(f"Error inesperado: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

