"""
Generador de variaciones de ejercicios con mayor complejidad.
Utiliza APIs de IA para generar variaciones inteligentes.
"""
import logging
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv
from pathlib import Path

# Imports for new Provider system
from .llm_providers import get_provider
from .utils.json_parser import extract_and_parse_json

# Cargar variables de entorno explícitamente desde el directorio del script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)



class VariationGenerator:
    """Genera variaciones de ejercicios con mayor complejidad."""
    
    def __init__(self, api_provider: str = "openai"):
        """
        Inicializa el generador.
        
        Args:
            api_provider: Proveedor de API ('openai', 'anthropic', 'gemini' o 'local')
        """
        self.api_provider = api_provider
        self.base_url = None # For local overrides
        self.local_model = None # For local overrides
        self.model_name = None # For overrides
        
        self._provider_instance = None
    
    def _get_provider(self):
        """
        Lazy loader para el proveedor, permitiendo configuración tardía de props.

        Returns:
            Instancia de LLMProvider si la inicialización fue exitosa
            None si hubo un error de configuración
        """
        if self._provider_instance:
            return self._provider_instance

        kwargs = {}
        if self.model_name:
            kwargs['model_name'] = self.model_name
        elif self.local_model and self.api_provider == 'local':
             kwargs['model_name'] = self.local_model

        if self.base_url:
            kwargs['base_url'] = self.base_url

        try:
            self._provider_instance = get_provider(self.api_provider, **kwargs)
            logger.info(f"[VariationGenerator] Proveedor inicializado: {self.api_provider}")
            return self._provider_instance
        except ValueError as e:
            logger.error(f"[VariationGenerator] Error inicializando proveedor '{self.api_provider}': {e}")
            return None
        except Exception as e:
            logger.error(f"[VariationGenerator] Error inesperado inicializando proveedor '{self.api_provider}': {e}")
            return None

    def _create_prompt(self, exercise: Dict, analysis: Dict) -> str:
        """Crea el prompt para generar una variación."""
        
        content = exercise.get('content', '')
        complexity = analysis.get('total_complexity', 0)
        concepts = ", ".join(analysis.get('concepts', []))
        
        prompt = f"""Actúa como un profesor experto de física y matemáticas universitarias.
Tu tarea es crear una VARIACIÓN de un ejercicio existente.

EJERCICIO ORIGINAL:
{content}

ANÁLISIS DE COMPLEJIDAD ORIGINAL:
- Complejidad: {complexity:.2f}
- Conceptos: {concepts}

OBJETIVO:
Generar una nueva versión del ejercicio que sea MÁS COMPLEJA y DESAFIANTE, pero evaluando los mismos principios fundamentales.

ESTRATEGIAS PARA AUMENTAR COMPLEJIDAD:
1. Cambia las variables numéricas por parámetros simbólicos (a, b, R, etc.)
2. Introduce sistemas de coordenadas diferentes (cilíndricas/esféricas) si aplica
3. Combina múltiples conceptos en un solo problema
4. Agrega una restricción o condición de borde adicional
5. Pide una generalización del resultado

REGLAS DE FORMATO:
1. Usa Markdown estándar
2. Usa LaTeX para matemáticas (bloques :::math o $$...$$)
3. La salida debe contener DOS PARTES separadas por "SOLUCIÓN REQUERIDA:"
   - Parte 1: El enunciado del nuevo ejercicio (encabezado con "EJERCICIO VARIADO:")
   - Parte 2: La solución paso a paso
   
Genera solo el contenido solicitado."""
        return prompt

    def _create_quiz_prompt(self, context_info: Dict[str, Any]) -> str:
        """Crea prompt para ejercicios de selección única."""
        content = context_info.get('content', '')
        
        prompt = f"""Actúa como un profesor experto. Genera una pregunta de examen de tipo SELECCIÓN ÚNICA (Quiz) basada en el siguiente material:

MATERIAL BASE:
{content}

REQUISITOS:
1. La pregunta debe ser conceptual y desafiante.
2. Genera 4 opciones (A, B, C, D).
3. Solo una opción debe ser correcta, las otras deben ser distractores plausibles.
4. Devuelve la respuesta EXCLUSIVAMENTE en formato JSON válido:
{{
  "question": "Enunciado de la pregunta en Markdown...",
  "options": {{
    "A": "Texto opción A",
    "B": "Texto opción B",
    "C": "Texto opción C",
    "D": "Texto opción D"
  }},
  "correct_option": "A",
  "explanation": "Explicación detallada de por qué es la correcta..."
}}
"""
        return prompt

    def generate_variation(self, exercise: Dict[str, Any], analysis: Dict[str, Any], exercise_type: str = "development", max_tokens: int = 2000) -> Optional[Dict]:
        """
        Genera una variación de un ejercicio existente.
        """
         # 1. Crear prompt según tipo
        if exercise_type == 'multiple_choice':
            context_info = {
                'content': f"Ejercicio Original:\n{exercise.get('content')}"
            }
            prompt = self._create_quiz_prompt(context_info)
        else:
            prompt = self._create_prompt(exercise, analysis)

        # 2. Get Provider
        provider = self._get_provider()
        if not provider:
            logger.warning("[VariationGenerator] Proveedor no inicializado, no se puede generar variación")
            return None

        # 3. Generar
        content = provider.generate_content(prompt, system_prompt="Eres un experto en diseño de exámenes de ingeniería.", max_tokens=max_tokens)

        if not content:
            logger.warning("[VariationGenerator] Proveedor retornó contenido vacío")
            return None

        # 4. Parsear respuesta
        variation_content = ""
        variation_solution = ""
        
        if exercise_type == 'multiple_choice':
            data = extract_and_parse_json(content)
            if data and 'question' in data:
                variation_content = f"{data['question']}\n\n"
                for opt, text in data.get('options', {}).items():
                    variation_content += f"- **{opt})** {text}\n"
                variation_solution = f"**Respuesta Correcta: {data.get('correct_option', '?')}**\n\n{data.get('explanation', '')}"
            else:
                variation_content = content
                variation_solution = "Error parseando JSON de quiz."
        else:
            # Parseo texto plano
            parts = content.split("SOLUCIÓN REQUERIDA:")
            if len(parts) == 2:
                variation_content = parts[0].replace("EJERCICIO VARIADO:", "").strip()
                variation_solution = parts[1].strip()
            else:
                variation_content = content
                variation_solution = ""

        return {
            'variation_content': variation_content,
            'variation_solution': variation_solution,
            'original_frontmatter': exercise.get('frontmatter', {}),
            'original_label': exercise.get('label'),
            'type': exercise_type
        }

    def _create_new_exercise_prompt(self, topic: str, tags: list, context: Dict, difficulty: str) -> str:
        """Crea prompt para ejercicio nuevo desde cero."""
        tags_str = ", ".join(tags)
        
        prompt = f"""Diseña un NUEVO ejercicio de examen universitario para:
Asignatura/Tema: {topic}
Conceptos Clave (Tags): {tags_str}
Nivel de Dificultad: {difficulty.upper()} (donde ALTA implica demostraciones o conexiones no triviales).

INSTRUCCIONES:
1. Crea un problema original que evalúe comprensión profunda.
2. No copies ejercicios de libros de texto.
3. Formato de salida:
   EJERCICIO NUEVO:
   [Enunciado en Markdown con LaTeX]
   
   SOLUCIÓN REQUERIDA:
   [Solución paso a paso]
"""
        return prompt

    def generate_new_exercise_from_topic(self, topic: str, tags: Optional[List[str]] = None, difficulty: str = "alta", exercise_type: str = "development", max_tokens: int = 2000) -> Optional[Dict]:
        """
        Genera un ejercicio nuevo desde cero.
        """
        tags = tags or []
        context = {} # Base implementations doesn't use context
        
        # 1. Crear prompt
        if exercise_type == 'multiple_choice':
             context_info = {
                'content': f"Tema: {topic}\nTags: {', '.join(tags)}\nDificultad: {difficulty}"
            }
             prompt = self._create_quiz_prompt(context_info)
        else:
             prompt = self._create_new_exercise_prompt(topic, tags, context, difficulty)
             
        # 2. Get Provider
        provider = self._get_provider()
        if not provider: return None
        
        # 3. Generar
        content = provider.generate_content(prompt, max_tokens=max_tokens)
        if not content: return None
        
        # 4. Parsear
        # Reutilizamos lógica simple de parseo
        if exercise_type == 'multiple_choice':
            data = extract_and_parse_json(content)
            if data and 'question' in data:
                 var_content = f"{data['question']}\n\n"
                 # ... (simplificado, igual que arriba)
                 for k, v in data.get('options',{}).items():
                     var_content += f"- **{k})** {v}\n"
                 var_sol = f"R: {data.get('correct_option')}. {data.get('explanation')}"
            else:
                 var_content = content
                 var_sol = ""
        else:
            parts = content.split("SOLUCIÓN REQUERIDA:")
            if len(parts) == 2:
                var_content = parts[0].replace("EJERCICIO NUEVO:", "").strip()
                var_sol = parts[1].strip()
            else:
                var_content = content
                var_sol = ""
                
        return {
             'variation_content': var_content,
             'variation_solution': var_sol,
             'original_frontmatter': {'topic': topic, 'tags': tags},
             'type': exercise_type
        }

    def generate_variation_with_solution(self, exercise: Dict, analysis: Dict, max_tokens: int = 2000) -> Optional[Dict]:
        """
        Genera una variación con su solución.
        """
        # Primero generar el ejercicio
        variation = self.generate_variation(exercise, analysis, max_tokens=max_tokens)
        
        if not variation:
            return None
            
        # Si ya tiene solución (porque el prompt único la pidió), retornarla
        if variation.get('variation_solution'):
            return variation
            
        provider = self._get_provider()
        if not provider: return None
        
        # Si no, generar la solución por separado (fallback legacy)
        solution_prompt = f"""Eres un experto en métodos matemáticos. Resuelve el siguiente ejercicio paso a paso:
        
EJERCICIO:
{variation['variation_content']}

GENERA LA SOLUCIÓN COMPLETA:"""
        
        solution_content = provider.generate_content(solution_prompt, max_tokens=max_tokens)
        
        if solution_content:
            variation['variation_solution'] = solution_content
        
        return variation

