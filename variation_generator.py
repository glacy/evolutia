"""
Generador de variaciones de ejercicios con mayor complejidad.
Utiliza APIs de IA para generar variaciones inteligentes.
"""
import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

from pathlib import Path

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
            api_provider: Proveedor de API ('openai', 'anthropic' o 'local')
            base_url: URL base para proveedor local
            local_model: Nombre del modelo para proveedor local
        """
        self.api_provider = api_provider
        self.api_key = None
        self.base_url = None
        self.local_model = None
        self.model_name = None
        self._setup_api()
    
    def _setup_api(self):
        """Configura la API según el proveedor seleccionado."""
        if self.api_provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                logger.warning("OPENAI_API_KEY no encontrada en variables de entorno")
        elif self.api_provider == "anthropic":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.warning("ANTHROPIC_API_KEY no encontrada en variables de entorno")
            else:
                logger.info(f"ANTHROPIC_API_KEY cargada: {self.api_key[:4]}...{self.api_key[-4:]}")
        elif self.api_provider == "local":
            # Para local, intentamos leer de config si no se pasaron args,
            # pero aquí asumimos que se configuran en __init__ o usan defaults.
            # En una implementación más robusta, pasaríamos config al constructor.
            self.api_key = "not-needed"
            # base_url y model se setean en __init__ o se usan defaults del método de llamada
        elif self.api_provider == "gemini":
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                logger.warning("GOOGLE_API_KEY no encontrada en variables de entorno")
            else:
                logger.info("GOOGLE_API_KEY cargada correctamente")
        else:
            logger.warning(f"Proveedor de API desconocido: {self.api_provider}")
    
    def _create_prompt(self, exercise: Dict, analysis: Dict) -> str:
        """
        Crea el prompt para la generación de variaciones.
        
        Args:
            exercise: Información del ejercicio original
            analysis: Análisis de complejidad del ejercicio
            
        Returns:
            Prompt estructurado para la IA
        """
        content = exercise.get('content', '')
        solution = exercise.get('solution', '')
        
        prompt = f"""Eres un experto en métodos matemáticos para física e ingeniería. Tu tarea es crear una variación de un ejercicio que sea MÁS COMPLEJA que el original, pero manteniendo el mismo tipo de problema y conceptos fundamentales.

EJERCICIO ORIGINAL:
{content}

SOLUCIÓN ORIGINAL (para referencia):
{solution[:1000] if solution else "No disponible"}

ANÁLISIS DEL EJERCICIO ORIGINAL:
- Tipo: {analysis.get('type', 'desconocido')}
- Pasos en solución: {analysis.get('solution_steps', 0)}
- Variables: {', '.join(analysis.get('variables', [])[:10])}
- Conceptos: {', '.join(analysis.get('concepts', []))}
- Complejidad matemática: {analysis.get('math_complexity', 0):.2f}

INSTRUCCIONES PARA LA VARIACIÓN:
1. AUMENTA la complejidad matemática de una o más de estas formas:
   - Agrega más variables independientes
   - Combina múltiples teoremas o conceptos en un solo ejercicio
   - Agrega pasos intermedios adicionales
   - Introduce condiciones especiales o casos límite
   - Modifica sistemas de coordenadas (de cartesianas a cilíndricas/esféricas, etc.)
   - Aumenta el número de dimensiones o componentes

2. MANTÉN:
   - El mismo tipo de ejercicio (demostración, cálculo, aplicación)
   - Los conceptos matemáticos fundamentales
   - El formato y estilo del ejercicio original
   - El uso de notación matemática LaTeX correcta

3. FORMATO:
   - Usa bloques de matemáticas con :::{{math}} para ecuaciones display
   - Usa $...$ para matemáticas inline
   - Mantén el español como idioma
   - Incluye contexto físico o de ingeniería si aplica

GENERA SOLO EL ENUNCIADO DEL EJERCICIO VARIADO (sin solución). El ejercicio debe ser claramente más complejo que el original."""
        
        return prompt
    
    def _create_quiz_prompt(self, context_info: Dict) -> str:
        """
        Crea el prompt para ejercicios de selección única.
        
        Args:
            context_info: Diccionario con info del ejercicio base o tema
            
        Returns:
            Prompt para generar JSON
        """
        content = context_info.get('content', '')
        
        prompt = f"""Eres un experto docente universitario en física y matemáticas.
Tu tarea es crear una pregunta de SELECCIÓN ÚNICA (Multiple Choice) de alta calidad y complejidad, basada en el siguiente contexto o ejercicio:

CONTEXTO/EJERCICIO BASE:
{content}

REQUISITOS:
1. Nivel: Universitario avanzado.
2. ENFOQUE: CONCEPTUAL. La pregunta debe evaluar la comprensión profunda de conceptos, teoremas, definiciones o propiedades.
   - EVITA preguntas que requieran cálculos largos o procedimentales.
   - PREFIERE preguntas sobre implicaciones teóricas, relaciones entre conceptos, o interpretaciones físicas.
   - ESTILO: Directo, conciso, tipo "completar la frase" o "seleccionar la afirmación verdadera".

EJEMPLO DE ESTILO DESEADO:
"El producto escalar de vectores perpendiculares es __________."
Opciones:
A) nulo
B) unitario
C) positivo
D) negativo

3. Formato: Selección única con 4 opciones (A, B, C, D).
4. Solo UNA opción debe ser correcta.
5. Las otras 3 opciones (distractores) deben ser plausibles y basadas en errores conceptuales comunes.
6. Incluye una retroalimentación/explicación detallada.

SALIDA OBLIGATORIA: JSON
Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura (sin bloques de código markdown):

{{
  "question": "Enunciado de la pregunta en LaTeX/MyST...",
  "options": {{
    "A": "Opción A...",
    "B": "Opción B...",
    "C": "Opción C...",
    "D": "Opción D..."
  }},
  "correct_option": "A",
  "explanation": "Explicación detallada..."
}}
"""
        return prompt
    
    def _call_openai_api(self, prompt: str, model: str = "gpt-4") -> Optional[str]:
        """
        Llama a la API de OpenAI.
        
        Args:
            prompt: Prompt para la generación
            model: Modelo a usar
            
        Returns:
            Respuesta generada o None si hay error
        """
        try:
            from openai import OpenAI
            
            if not self.api_key:
                logger.error("OpenAI API key no configurada")
                return None
            
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en métodos matemáticos para física e ingeniería. Generas ejercicios académicos de alta calidad con notación matemática LaTeX correcta."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
        except ImportError:
            logger.error("Biblioteca openai no instalada. Instala con: pip install openai")
            return None
        except Exception as e:
            logger.error(f"Error llamando a OpenAI API: {e}")
            return None

    def _call_local_api(self, prompt: str) -> Optional[str]:
        """
        Llama a una API local compatible con OpenAI.
        """
        try:
            from openai import OpenAI
            
            # Usar defaults si no están configurados
            base_url = self.base_url or "http://localhost:11434/"
            model = self.local_model or "llama3"
            
            client = OpenAI(
                base_url=base_url,
                api_key="not-needed",
                timeout=300.0  # 5 minutos timeout
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en métodos matemáticos para física e ingeniería. Generas ejercicios académicos de alta calidad con notación matemática LaTeX correcta."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
        except ImportError:
            logger.error("Biblioteca openai no instalada. Instala con: pip install openai")
            return None
        except Exception as e:
            logger.error(f"Error llamando a Local API: {e}")
            return None
    
    def _call_anthropic_api(self, prompt: str, model: str = "claude-3-opus-20240229") -> Optional[str]:
        """
        Llama a la API de Anthropic (Claude).
        
        Args:
            prompt: Prompt para la generación
            model: Modelo a usar
            
        Returns:
            Respuesta generada o None si hay error
        """
        try:
            import anthropic
            
            if not self.api_key:
                logger.error("Anthropic API key no configurada")
                return None
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            message = client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0.7,
                system="Eres un experto en métodos matemáticos para física e ingeniería. Generas ejercicios académicos de alta calidad con notación matemática LaTeX correcta.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text.strip()
        except ImportError:
            logger.error("Biblioteca anthropic no instalada. Instala con: pip install anthropic")
            return None
        except Exception as e:
            logger.error(f"Error llamando a Anthropic API: {e}")
            return None
            logger.error(f"Error llamando a Anthropic API: {e}")
            return None
    
    def _call_gemini_api(self, prompt: str, model: str = "gemini-2.5-pro") -> Optional[str]:
        """
        Llama a la API de Google Gemini.
        """
        try:
            import google.generativeai as genai
            import os
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY no configurada")
                return None
            
            genai.configure(api_key=api_key)
            
            model_name = model or "gemini-2.5-pro"
            if model_name == 'gemini': model_name = "gemini-2.5-pro"

            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
            
            model_instance = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
            )
            
            response = model_instance.generate_content(prompt)
            
            return response.text
        except Exception as e:
            logger.error(f"Error llamando a Gemini API: {e}")
            return None

    def generate_variation(self, exercise: Dict, analysis: Dict, exercise_type: str = "development") -> Optional[Dict]:
        """
        Genera una variación más compleja de un ejercicio.
        
        Args:
            exercise: Información del ejercicio original (content, solution, metadata)
            analysis: Análisis de complejidad del ejercicio original
            exercise_type: Tipo de ejercicio ('development' o 'multiple_choice')
            
        Returns:
            Diccionario con la variación generada o None si hay error
        """
        # 1. Crear prompt
        if exercise_type == 'multiple_choice':
             context_info = {
                'content': f"Ejercicio Base:\n{exercise.get('content')}\n\nSolución Base:\n{(exercise.get('solution') or '')[:500]}..."
            }
             prompt = self._create_quiz_prompt(context_info)
        else:
            prompt = self._create_prompt(exercise, analysis)
        
        if self.api_provider == "openai":
            variation_content = self._call_openai_api(prompt, model=self.model_name or "gpt-4")
        elif self.api_provider == "anthropic":
            variation_content = self._call_anthropic_api(prompt, model=self.model_name or "claude-3-opus-20240229")
        elif self.api_provider == "local":
            variation_content = self._call_local_api(prompt)
        elif self.api_provider == "gemini":
            variation_content = self._call_gemini_api(prompt, model=self.model_name)
        else:
            logger.error(f"Proveedor de API no soportado: {self.api_provider}")
            variation_content = None
        
        if not variation_content:
            return None

        # Parsear si es quiz
        variation_solution = "Solución no generada en modo simple."
        
        if exercise_type == 'multiple_choice':
            try:
                import json
                import re
                clean_content = variation_content.replace('```json', '').replace('```', '').strip()
                
                # Fix common latex backslash issues in json string
                # Retain escaped unicode but double escape other backslashes if single
                # Simple approach: use raw string or manual Escape for parsing if validation fails
                
                # strict=False helps with newlines. For backslashes:
                # If LLM returns: "question": "\frac{1}{2}" -> JSON sees \f (formfeed).
                # To be valid JSON it should be "\\frac{1}{2}".
                # We try to fix single backslashes that are not valid escapes.
                # Only if strict load fails? Or pre-process.
                # A safe heuristic: replace single \ with \\ if not followed by " or \ or / or b/f/n/r/t/u
                
                try:
                     data = json.loads(clean_content, strict=False)
                except json.JSONDecodeError:
                    # Fallback: escape all backslashes that might be latex
                    escaped_content = clean_content.replace('\\', '\\\\') 
                    # But this double escapes valid json escapes like \" -> \\" which breaks string end
                    # Better: use a specialized parser or regex fix? 
                    # Simple fix: if it fails, try lenient regex extraction or manual string parsing
                    # For now, let's try strict=False with a simple replace for common latex cmds
                    clean_content_fixed = clean_content.replace('\\', '\\\\').replace('\\\\"', '\\"')
                    data = json.loads(clean_content_fixed, strict=False)

                variation_content = f"{data['question']}\n\n"
                for opt, text in data['options'].items():
                    variation_content += f"- **{opt})** {text}\n"
                
                variation_solution = f"**Respuesta Correcta: {data['correct_option']}**\n\n{data['explanation']}"
            except Exception as e:
                logger.error(f"Error parseando JSON de quiz en base variation: {e}")
                # variation_content se queda con el raw
        
        return {
            'variation_content': variation_content,
            'variation_solution': variation_solution,
            'original_frontmatter': exercise.get('frontmatter', {}),
            'type': exercise_type
        }
    
    def generate_variation_with_solution(self, exercise: Dict, analysis: Dict) -> Optional[Dict]:
        """
        Genera una variación con su solución.
        
        Args:
            exercise: Información del ejercicio original
            analysis: Análisis de complejidad del ejercicio original
            
        Returns:
            Diccionario con variación y solución o None si hay error
        """
        # Primero generar el ejercicio
        variation = self.generate_variation(exercise, analysis)
        
        if not variation:
            return None
        
        # Luego generar la solución
        solution_prompt = f"""Eres un experto en métodos matemáticos para física e ingeniería. Resuelve el siguiente ejercicio paso a paso, mostrando todos los cálculos y procedimientos.

EJERCICIO:
{variation['variation_content']}

INSTRUCCIONES:
1. Resuelve el ejercicio de forma completa y detallada
2. Muestra todos los pasos intermedios
3. Usa notación matemática LaTeX correcta
4. Explica el razonamiento cuando sea necesario
5. Usa bloques :::{{math}} para ecuaciones display y $...$ para inline
6. Escribe en español

GENERA LA SOLUCIÓN COMPLETA:"""
        
        if self.api_provider == "openai":
            solution_content = self._call_openai_api(solution_prompt, model=self.model_name or "gpt-4")
        elif self.api_provider == "anthropic":
            solution_content = self._call_anthropic_api(solution_prompt, model=self.model_name or "claude-3-opus-20240229")
        elif self.api_provider == "local":
            solution_content = self._call_local_api(solution_prompt)
        else:
            solution_content = None
        
        if solution_content:
            variation['variation_solution'] = solution_content
        
        return variation

