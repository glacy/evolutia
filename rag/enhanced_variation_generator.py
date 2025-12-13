"""
Enhanced Variation Generator: Genera variaciones usando RAG.
"""
import logging
from typing import Dict, Optional

try:
    from variation_generator import VariationGenerator
except ImportError:
    try:
        from ..variation_generator import VariationGenerator
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from variation_generator import VariationGenerator

try:
    from rag.rag_retriever import RAGRetriever
    from rag.context_enricher import ContextEnricher
except ImportError:
    try:
        from .rag_retriever import RAGRetriever
        from .context_enricher import ContextEnricher
    except ImportError:
        from rag_retriever import RAGRetriever
        from context_enricher import ContextEnricher

logger = logging.getLogger(__name__)


class EnhancedVariationGenerator(VariationGenerator):
    """Genera variaciones usando RAG para enriquecer el contexto."""
    
    def __init__(self, api_provider: str = "openai", retriever: RAGRetriever = None,
                 context_enricher: ContextEnricher = None):
        """
        Inicializa el generador mejorado.
        
        Args:
            api_provider: Proveedor de API ('openai' o 'anthropic')
            retriever: Instancia de RAGRetriever
            context_enricher: Instancia de ContextEnricher
        """
        super().__init__(api_provider)
        self.retriever = retriever
        self.context_enricher = context_enricher or ContextEnricher()
    
    def _retrieve_context(self, exercise: Dict, analysis: Dict) -> Dict:
        """
        Recupera contexto relevante usando RAG.
        
        Args:
            exercise: Información del ejercicio original
            analysis: Análisis de complejidad
            
        Returns:
            Diccionario con contexto recuperado
        """
        if not self.retriever:
            return {}
        
        context = {}
        
        try:
            # Buscar ejercicios similares
            exercise_content = exercise.get('content', '')
            similar = self.retriever.retrieve_similar_exercises(
                exercise_content,
                exclude_label=exercise.get('label'),
                top_k=5
            )
            context['similar_exercises'] = similar
            
            # Buscar conceptos relacionados
            concepts = analysis.get('concepts', [])
            if concepts:
                related = self.retriever.retrieve_related_concepts(concepts, top_k=3)
                context['related_concepts'] = related
            
            # Buscar contexto de lecturas
            topic = exercise.get('source_file', {}).name if hasattr(exercise.get('source_file'), 'name') else ''
            if topic:
                reading_context = self.retriever.retrieve_reading_context(topic, top_k=2)
                context['reading_context'] = reading_context
            
            # Buscar ejercicios con complejidad similar (para referencia)
            target_complexity = analysis.get('total_complexity', 0)
            if target_complexity > 0:
                complexity_examples = self.retriever.retrieve_by_complexity(
                    target_complexity,
                    tolerance=0.3,
                    top_k=3
                )
                context['complexity_examples'] = complexity_examples
        
        except Exception as e:
            logger.warning(f"Error recuperando contexto RAG: {e}")
            context = {}
        
        return context
    
    def _create_prompt(self, exercise: Dict, analysis: Dict) -> str:
        """
        Crea el prompt enriquecido con contexto RAG.
        
        Args:
            exercise: Información del ejercicio original
            analysis: Análisis de complejidad del ejercicio
            
        Returns:
            Prompt enriquecido
        """
        # Crear prompt base usando el método del padre
        base_prompt = super()._create_prompt(exercise, analysis)
        
        # Si no hay retriever, usar prompt base
        if not self.retriever:
            return base_prompt
        
        # Recuperar contexto
        context = self._retrieve_context(exercise, analysis)
        
        # Enriquecer prompt con contexto
        enriched_prompt = self.context_enricher.create_enriched_prompt(
            base_prompt,
            exercise,
            analysis,
            context
        )
        
        return enriched_prompt
    
    def generate_variation(self, exercise: Dict, analysis: Dict) -> Optional[Dict]:
        """
        Genera una variación más compleja usando RAG.
        
        Args:
            exercise: Información del ejercicio original
            analysis: Análisis de complejidad del ejercicio original
            
        Returns:
            Diccionario con la variación generada o None si hay error
        """
        # El método _create_prompt ya está sobrescrito para usar RAG
        # Así que solo llamamos al método del padre que usa nuestro prompt enriquecido
        variation = super().generate_variation(exercise, analysis)
        
        if variation and self.retriever:
            # Agregar información sobre el contexto usado
            context = self._retrieve_context(exercise, analysis)
            variation['rag_context'] = {
                'similar_exercises_count': len(context.get('similar_exercises', [])),
                'related_concepts_count': len(context.get('related_concepts', [])),
                'reading_context_count': len(context.get('reading_context', []))
            }
        
        return variation
    
    def generate_variation_with_solution(self, exercise: Dict, analysis: Dict) -> Optional[Dict]:
        """
        Genera una variación con su solución usando RAG.
        
        Args:
            exercise: Información del ejercicio original
            analysis: Análisis de complejidad del ejercicio original
            
        Returns:
            Diccionario con variación y solución o None si hay error
        """
        # Generar variación (ya usa RAG)
        variation = self.generate_variation(exercise, analysis)
        
        if not variation:
            return None
        
        # Generar solución (usar método del padre)
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

