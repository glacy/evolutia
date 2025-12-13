"""
Consistency Validator: Valida consistencia usando RAG.
"""
import logging
from typing import Dict, List, Optional

try:
    from complexity_validator import ComplexityValidator
except ImportError:
    try:
        from ..complexity_validator import ComplexityValidator
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from complexity_validator import ComplexityValidator

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


class ConsistencyValidator(ComplexityValidator):
    """Valida consistencia usando RAG además de validación de complejidad."""
    
    def __init__(self, retriever: RAGRetriever = None, context_enricher: ContextEnricher = None):
        """
        Inicializa el validador de consistencia.
        
        Args:
            retriever: Instancia de RAGRetriever
            context_enricher: Instancia de ContextEnricher
        """
        super().__init__()
        self.retriever = retriever
        self.context_enricher = context_enricher or ContextEnricher()
    
    def validate_consistency(self, variation_content: str, original_exercise: Dict,
                           original_analysis: Dict) -> Dict:
        """
        Valida consistencia de la variación con ejercicios similares del curso.
        
        Args:
            variation_content: Contenido de la variación generada
            original_exercise: Ejercicio original
            original_analysis: Análisis del ejercicio original
            
        Returns:
            Diccionario con resultados de validación de consistencia
        """
        if not self.retriever:
            return {
                'is_consistent': True,
                'reason': 'RAG no disponible, saltando validación de consistencia',
                'similarity_scores': [],
                'warnings': []
            }
        
        try:
            # Buscar ejercicios similares a la variación
            similar_exercises = self.retriever.retrieve_similar_exercises(
                variation_content,
                exclude_label=original_exercise.get('label'),
                top_k=5
            )
            
            if not similar_exercises:
                return {
                    'is_consistent': True,
                    'reason': 'No se encontraron ejercicios similares para comparar',
                    'similarity_scores': [],
                    'warnings': []
                }
            
            # Analizar similitudes
            similarity_scores = [ex.get('similarity', 0) for ex in similar_exercises]
            avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
            
            # Verificar consistencia de complejidad
            complexity_warnings = []
            variation_complexity = original_analysis.get('total_complexity', 0) * 1.2  # Estimación
            
            for exercise in similar_exercises[:3]:  # Top 3
                ex_complexity = float(exercise.get('metadata', {}).get('complexity', 0))
                if ex_complexity > 0:
                    diff = abs(variation_complexity - ex_complexity) / ex_complexity
                    if diff > 0.5:  # Más del 50% de diferencia
                        complexity_warnings.append(
                            f"Complejidad muy diferente de ejercicio similar "
                            f"(variación: {variation_complexity:.2f}, similar: {ex_complexity:.2f})"
                        )
            
            # Verificar consistencia de conceptos
            concept_warnings = []
            original_concepts = set(original_analysis.get('concepts', []))
            
            for exercise in similar_exercises[:3]:
                ex_concepts = set(
                    exercise.get('metadata', {}).get('concepts', '').split(',')
                    if exercise.get('metadata', {}).get('concepts') else []
                )
                ex_concepts = {c.strip() for c in ex_concepts if c.strip()}
                
                # Verificar si hay conceptos muy diferentes
                if ex_concepts and original_concepts:
                    overlap = len(original_concepts & ex_concepts) / len(original_concepts | ex_concepts)
                    if overlap < 0.3:  # Menos del 30% de overlap
                        concept_warnings.append(
                            f"Conceptos muy diferentes de ejercicios similares "
                            f"(overlap: {overlap:.2f})"
                        )
            
            # Determinar si es consistente
            is_consistent = (
                avg_similarity >= 0.5 and  # Al menos 50% de similitud promedio
                len(complexity_warnings) < 2 and  # No demasiadas advertencias de complejidad
                len(concept_warnings) < 2  # No demasiadas advertencias de conceptos
            )
            
            return {
                'is_consistent': is_consistent,
                'avg_similarity': avg_similarity,
                'similarity_scores': similarity_scores,
                'similar_exercises_count': len(similar_exercises),
                'complexity_warnings': complexity_warnings,
                'concept_warnings': concept_warnings,
                'warnings': complexity_warnings + concept_warnings
            }
        
        except Exception as e:
            logger.error(f"Error en validación de consistencia: {e}")
            return {
                'is_consistent': True,  # Por defecto, asumir consistente si hay error
                'reason': f'Error en validación: {str(e)}',
                'similarity_scores': [],
                'warnings': []
            }
    
    def validate(self, original_exercise: Dict, original_analysis: Dict,
                 variation: Dict) -> Dict:
        """
        Valida variación usando tanto complejidad como consistencia RAG.
        
        Args:
            original_exercise: Ejercicio original
            original_analysis: Análisis del ejercicio original
            variation: Variación generada
            
        Returns:
            Diccionario con validación completa
        """
        # Primero validar complejidad (método del padre)
        complexity_validation = super().validate(
            original_exercise,
            original_analysis,
            variation
        )
        
        # Luego validar consistencia con RAG
        variation_content = variation.get('variation_content', '')
        consistency_validation = self.validate_consistency(
            variation_content,
            original_exercise,
            original_analysis
        )
        
        # Combinar resultados
        combined_validation = {
            **complexity_validation,
            'consistency': consistency_validation,
            'is_valid': (
                complexity_validation.get('is_valid', False) and
                consistency_validation.get('is_consistent', True)  # Consistencia es opcional
            )
        }
        
        # Agregar advertencias de consistencia
        if consistency_validation.get('warnings'):
            combined_validation['warnings'].extend(
                [f"Consistencia: {w}" for w in consistency_validation['warnings']]
            )
        
        # Agregar información de similitud
        if consistency_validation.get('avg_similarity'):
            combined_validation['rag_avg_similarity'] = consistency_validation['avg_similarity']
            combined_validation['improvements'].append(
                f"Similitud promedio con ejercicios del curso: {consistency_validation['avg_similarity']:.2f}"
            )
        
        return combined_validation

