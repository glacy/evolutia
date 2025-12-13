"""
Context Enricher: Enriquece prompts con contexto recuperado del RAG.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ContextEnricher:
    """Enriquece prompts con contexto recuperado."""
    
    def __init__(self, max_context_length: int = 3000):
        """
        Inicializa el enricher.
        
        Args:
            max_context_length: Longitud máxima del contexto (en caracteres)
        """
        self.max_context_length = max_context_length
    
    def enrich_with_similar_exercises(self, similar_exercises: List[Dict],
                                     max_examples: int = 3) -> str:
        """
        Formatea ejercicios similares para incluir en el prompt.
        
        Args:
            similar_exercises: Lista de ejercicios similares recuperados
            max_examples: Número máximo de ejemplos a incluir
            
        Returns:
            Texto formateado con ejercicios similares
        """
        if not similar_exercises:
            return ""
        
        # Ordenar por similitud y tomar los mejores
        sorted_exercises = sorted(
            similar_exercises,
            key=lambda x: x.get('similarity', 0),
            reverse=True
        )[:max_examples]
        
        context = "EJERCICIOS SIMILARES DEL CURSO (para referencia de estilo y nivel):\n\n"
        
        for i, exercise in enumerate(sorted_exercises, 1):
            content = exercise.get('content', '')
            metadata = exercise.get('metadata', {})
            similarity = exercise.get('similarity', 0)
            
            # Extraer solo el enunciado si es muy largo
            if len(content) > 500:
                # Intentar encontrar donde termina el enunciado
                parts = content.split('\n\n')
                if len(parts) > 1:
                    content = parts[0]  # Solo el enunciado
            
            context += f"Ejemplo {i} (similitud: {similarity:.2f}):\n"
            context += f"{content[:400]}\n\n"
        
        return context.strip()
    
    def enrich_with_related_concepts(self, related_docs: List[Dict],
                                    concepts: List[str]) -> str:
        """
        Formatea documentos relacionados con conceptos.
        
        Args:
            related_docs: Documentos relacionados recuperados
            concepts: Lista de conceptos buscados
            
        Returns:
            Texto formateado con conceptos relacionados
        """
        if not related_docs:
            return ""
        
        context = f"CONTEXTO TEÓRICO RELACIONADO CON LOS CONCEPTOS: {', '.join(concepts)}\n\n"
        
        # Agrupar por tipo
        exercises = [d for d in related_docs if d.get('metadata', {}).get('type') == 'exercise']
        readings = [d for d in related_docs if d.get('metadata', {}).get('type') == 'reading']
        
        if readings:
            context += "Información de lecturas:\n"
            for reading in readings[:2]:  # Máximo 2 chunks de lectura
                content = reading.get('content', '')
                context += f"- {content[:300]}...\n\n"
        
        if exercises:
            context += "Ejercicios relacionados:\n"
            for exercise in exercises[:2]:  # Máximo 2 ejercicios
                content = exercise.get('content', '')
                # Solo el enunciado
                if 'EJERCICIO:' in content:
                    content = content.split('SOLUCIÓN:')[0] if 'SOLUCIÓN:' in content else content
                context += f"- {content[:300]}...\n\n"
        
        return context.strip()
    
    def enrich_with_complexity_examples(self, complexity_examples: List[Dict]) -> str:
        """
        Formatea ejemplos de ejercicios con complejidad similar.
        
        Args:
            complexity_examples: Ejercicios con complejidad similar
            
        Returns:
            Texto formateado
        """
        if not complexity_examples:
            return ""
        
        context = "EJERCICIOS CON COMPLEJIDAD SIMILAR (para referencia de nivel):\n\n"
        
        for i, example in enumerate(complexity_examples[:2], 1):  # Máximo 2 ejemplos
            content = example.get('content', '')
            metadata = example.get('metadata', {})
            complexity = metadata.get('complexity', 'N/A')
            
            # Solo el enunciado
            if 'EJERCICIO:' in content:
                content = content.split('SOLUCIÓN:')[0] if 'SOLUCIÓN:' in content else content
            
            context += f"Ejemplo {i} (complejidad: {complexity}):\n"
            context += f"{content[:300]}...\n\n"
        
        return context.strip()
    
    def create_enriched_prompt(self, original_prompt: str, exercise: Dict,
                              analysis: Dict, retriever_results: Dict) -> str:
        """
        Crea un prompt enriquecido con todo el contexto recuperado.
        
        Args:
            original_prompt: Prompt original
            exercise: Ejercicio original
            analysis: Análisis del ejercicio
            retriever_results: Resultados del retriever con claves:
                - similar_exercises: Lista de ejercicios similares
                - related_concepts: Lista de documentos relacionados
                - reading_context: Lista de chunks de lectura
                - complexity_examples: Lista de ejercicios con complejidad similar
        
        Returns:
            Prompt enriquecido
        """
        enriched_parts = []
        
        # Agregar ejercicios similares
        similar = retriever_results.get('similar_exercises', [])
        if similar:
            similar_context = self.enrich_with_similar_exercises(similar)
            if similar_context:
                enriched_parts.append(similar_context)
        
        # Agregar conceptos relacionados
        concepts = analysis.get('concepts', [])
        related = retriever_results.get('related_concepts', [])
        if related and concepts:
            concepts_context = self.enrich_with_related_concepts(related, concepts)
            if concepts_context:
                enriched_parts.append(concepts_context)
        
        # Agregar contexto de lecturas
        readings = retriever_results.get('reading_context', [])
        if readings:
            reading_context = "CONTEXTO DE LECTURAS RELACIONADAS:\n\n"
            for reading in readings[:2]:
                content = reading.get('content', '')
                reading_context += f"- {content[:400]}...\n\n"
            enriched_parts.append(reading_context.strip())
        
        # Agregar ejemplos de complejidad
        complexity_examples = retriever_results.get('complexity_examples', [])
        if complexity_examples:
            complexity_context = self.enrich_with_complexity_examples(complexity_examples)
            if complexity_context:
                enriched_parts.append(complexity_context)
        
        # Combinar todo
        if not enriched_parts:
            return original_prompt
        
        # Insertar contexto antes de las instrucciones
        context_section = "\n\n" + "="*80 + "\n"
        context_section += "CONTEXTO ADICIONAL DEL CURSO:\n"
        context_section += "="*80 + "\n\n"
        context_section += "\n\n---\n\n".join(enriched_parts)
        context_section += "\n\n" + "="*80 + "\n"
        
        # Insertar después del análisis pero antes de las instrucciones
        insertion_point = original_prompt.find("INSTRUCCIONES PARA LA VARIACIÓN:")
        if insertion_point > 0:
            enriched_prompt = (
                original_prompt[:insertion_point] +
                context_section +
                original_prompt[insertion_point:]
            )
        else:
            # Si no encontramos el punto de inserción, agregar al final
            enriched_prompt = original_prompt + "\n\n" + context_section
        
        # Limitar longitud total
        if len(enriched_prompt) > self.max_context_length:
            logger.warning(f"Prompt enriquecido muy largo ({len(enriched_prompt)} chars), truncando...")
            # Mantener el prompt original y truncar solo el contexto
            original_length = len(original_prompt)
            max_context = self.max_context_length - original_length - 100
            if max_context > 0:
                context_section = context_section[:max_context] + "\n\n[Contexto truncado...]"
                insertion_point = original_prompt.find("INSTRUCCIONES PARA LA VARIACIÓN:")
                enriched_prompt = (
                    original_prompt[:insertion_point] +
                    context_section +
                    original_prompt[insertion_point:]
                )
            else:
                # Si no hay espacio, usar prompt original
                enriched_prompt = original_prompt
        
        return enriched_prompt
    
    def format_for_consistency_check(self, similar_exercises: List[Dict]) -> str:
        """
        Formatea ejercicios similares para validación de consistencia.
        
        Args:
            similar_exercises: Ejercicios similares del curso
            
        Returns:
            Texto formateado para comparación
        """
        if not similar_exercises:
            return "No hay ejercicios similares para comparar."
        
        formatted = "EJERCICIOS SIMILARES DEL CURSO PARA COMPARACIÓN:\n\n"
        
        for i, exercise in enumerate(similar_exercises[:5], 1):  # Top 5
            content = exercise.get('content', '')
            metadata = exercise.get('metadata', {})
            similarity = exercise.get('similarity', 0)
            
            # Extraer solo enunciado
            if 'EJERCICIO:' in content:
                content = content.split('SOLUCIÓN:')[0] if 'SOLUCIÓN:' in content else content
            
            formatted += f"{i}. Similitud: {similarity:.2f}\n"
            formatted += f"   Complejidad: {metadata.get('complexity', 'N/A')}\n"
            formatted += f"   Conceptos: {metadata.get('concepts', 'N/A')}\n"
            formatted += f"   Enunciado: {content[:200]}...\n\n"
        
        return formatted

