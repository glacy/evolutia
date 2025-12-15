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
    
    def generate_variation(self, exercise: Dict, analysis: Dict) -> Optional[Dict]:
        """
        Genera una variación más compleja del ejercicio.
        
        Args:
            exercise: Información del ejercicio original
            analysis: Análisis de complejidad del ejercicio original
            
        Returns:
            Diccionario con la variación generada o None si hay error
        """
        prompt = self._create_prompt(exercise, analysis)
        
        if self.api_provider == "openai":
            variation_content = self._call_openai_api(prompt, model=self.model_name or "gpt-4")
        elif self.api_provider == "anthropic":
            variation_content = self._call_anthropic_api(prompt, model=self.model_name or "claude-3-opus-20240229")
        elif self.api_provider == "local":
            variation_content = self._call_local_api(prompt)
        elif self.api_provider == "gemini":
            # Si se llama desde la clase base, lanzar error o implementar básico
            # En este caso, EnhancedVariationGenerator lo maneja, pero el base necesita no fallar
            logger.error("VariationGenerator base no implementa llamadas a Gemini directamente. Use EnhancedVariationGenerator.")
            variation_content = None
        else:
            logger.error(f"Proveedor de API no soportado: {self.api_provider}")
            variation_content = None
        
        if not variation_content:
            return None
        
        return {
            'original_label': exercise.get('label'),
            'original_content': exercise.get('content'),
            'variation_content': variation_content,
            'original_analysis': analysis,
            'original_frontmatter': exercise.get('frontmatter', {})
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

