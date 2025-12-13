"""
RAG Retriever: Busca información relevante del vector store.
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Recupera información relevante del vector store."""
    
    def __init__(self, config: Dict[str, Any], base_path: Path, chroma_client=None):
        """
        Inicializa el retriever.
        
        Args:
            config: Configuración de RAG desde config.yaml
            base_path: Ruta base del proyecto
            chroma_client: Cliente ChromaDB compartido (opcional)
        """
        self.config = config
        self.base_path = Path(base_path)
        self.embedding_provider = config.get('embeddings', {}).get('provider', 'openai')
        self.chroma_client = chroma_client
        self._setup_embeddings()
        self._setup_vector_store()
    
    def _setup_embeddings(self):
        """Configura el modelo de embeddings (debe coincidir con el indexer)."""
        embeddings_config = self.config.get('embeddings', {})
        provider = embeddings_config.get('provider', 'openai')
        model_name = embeddings_config.get('model', 'text-embedding-3-small')
        
        if provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("openai no está instalado")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY no encontrada")
            
            self.embedding_client = OpenAI(api_key=api_key)
            self.embedding_model_name = model_name
        
        elif provider == 'sentence-transformers':
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("sentence-transformers no está instalado")
            
            self.embedding_model = SentenceTransformer(model_name)
    
    def _setup_vector_store(self):
        """Configura la conexión al vector store."""
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb no está instalado")
        
        vs_config = self.config.get('vector_store', {})
        persist_dir = Path(vs_config.get('persist_directory', './storage/vector_store'))
        collection_name = vs_config.get('collection_name', 'ejercicios_mmfi')
        
        # Usar cliente compartido si está disponible, sino crear uno nuevo
        if self.chroma_client is not None:
            self.client = self.chroma_client
        else:
            self.client = chromadb.PersistentClient(
                path=str(persist_dir.resolve()),
                settings=Settings(anonymized_telemetry=False)
            )
        
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            raise ValueError(f"No se pudo cargar la colección {collection_name}. ¿Está indexado? Error: {e}")
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Genera embedding para una consulta.
        
        Args:
            query: Texto de consulta
            
        Returns:
            Embedding del query
        """
        if self.embedding_provider == 'openai':
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model_name,
                input=query
            )
            return response.data[0].embedding
        
        elif self.embedding_provider == 'sentence-transformers':
            return self.embedding_model.encode(query, show_progress_bar=False).tolist()
    
    def retrieve_similar_exercises(self, exercise_content: str, top_k: int = 5,
                                   exclude_label: Optional[str] = None,
                                   min_complexity: Optional[float] = None,
                                   max_complexity: Optional[float] = None) -> List[Dict]:
        """
        Recupera ejercicios similares al contenido dado.
        
        Args:
            exercise_content: Contenido del ejercicio de referencia
            top_k: Número de resultados a recuperar
            exclude_label: Label del ejercicio a excluir (el original)
            min_complexity: Complejidad mínima
            max_complexity: Complejidad máxima
            
        Returns:
            Lista de ejercicios similares con sus metadatos
        """
        retrieval_config = self.config.get('retrieval', {})
        top_k = retrieval_config.get('top_k', top_k)
        similarity_threshold = retrieval_config.get('similarity_threshold', 0.7)
        
        # Generar embedding del query
        query_embedding = self._generate_query_embedding(exercise_content)
        
        # Construir filtros de metadatos usando sintaxis correcta de ChromaDB
        conditions = [{'type': 'exercise'}]
        
        if exclude_label:
            conditions.append({'label': {'$ne': exclude_label}})
        
        if min_complexity is not None and max_complexity is not None:
            conditions.append({'complexity': {'$gte': float(min_complexity)}})
            conditions.append({'complexity': {'$lte': float(max_complexity)}})
        elif min_complexity is not None:
            conditions.append({'complexity': {'$gte': float(min_complexity)}})
        elif max_complexity is not None:
            conditions.append({'complexity': {'$lte': float(max_complexity)}})
        
        # Si hay múltiples condiciones, usar $and
        if len(conditions) > 1:
            where = {'$and': conditions}
        elif len(conditions) == 1:
            where = conditions[0]
        else:
            where = None
        
        # Buscar en el vector store
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # Buscar más para filtrar después
            where=where
        )
        
        # Procesar resultados
        similar_exercises = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, (doc_id, doc, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Filtrar por umbral de similitud (distance es distancia, menor = más similar)
                similarity = 1 - distance  # Convertir distancia a similitud
                
                if similarity >= similarity_threshold:
                    similar_exercises.append({
                        'id': doc_id,
                        'content': doc,
                        'metadata': metadata,
                        'similarity': similarity,
                        'distance': distance
                    })
                
                if len(similar_exercises) >= top_k:
                    break
        
        logger.info(f"Recuperados {len(similar_exercises)} ejercicios similares")
        return similar_exercises
    
    def retrieve_related_concepts(self, concepts: List[str], top_k: int = 3) -> List[Dict]:
        """
        Recupera ejercicios o lecturas relacionados con conceptos específicos.
        
        Args:
            concepts: Lista de conceptos a buscar
            top_k: Número de resultados por concepto
            
        Returns:
            Lista de documentos relacionados
        """
        query = f"Conceptos: {', '.join(concepts)}"
        query_embedding = self._generate_query_embedding(query)
        
        retrieval_config = self.config.get('retrieval', {})
        top_k_total = retrieval_config.get('top_k', top_k * len(concepts))
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k_total
        )
        
        related_docs = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for doc_id, doc, metadata, distance in zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                similarity = 1 - distance
                related_docs.append({
                    'id': doc_id,
                    'content': doc,
                    'metadata': metadata,
                    'similarity': similarity
                })
        
        logger.info(f"Recuperados {len(related_docs)} documentos relacionados con conceptos")
        return related_docs
    
    def retrieve_reading_context(self, topic: str, top_k: int = 2) -> List[Dict]:
        """
        Recupera contexto de lecturas relacionadas con un tema.
        
        Args:
            topic: Tema o concepto
            top_k: Número de chunks de lectura a recuperar
            
        Returns:
            Lista de chunks de lecturas
        """
        query_embedding = self._generate_query_embedding(topic)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={'type': 'reading'}
        )
        
        reading_chunks = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for doc_id, doc, metadata, distance in zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                reading_chunks.append({
                    'id': doc_id,
                    'content': doc,
                    'metadata': metadata,
                    'similarity': 1 - distance
                })
        
        logger.info(f"Recuperados {len(reading_chunks)} chunks de lecturas")
        return reading_chunks
    
    def retrieve_by_complexity(self, target_complexity: float, tolerance: float = 0.2,
                               top_k: int = 5) -> List[Dict]:
        """
        Recupera ejercicios con complejidad similar a la objetivo.
        
        Args:
            target_complexity: Complejidad objetivo
            tolerance: Tolerancia en la complejidad
            top_k: Número de resultados
            
        Returns:
            Lista de ejercicios con complejidad similar
        """
        min_complexity = target_complexity * (1 - tolerance)
        max_complexity = target_complexity * (1 + tolerance)
        
        # Usar búsqueda por metadatos con sintaxis correcta de ChromaDB
        where = {
            '$and': [
                {'type': 'exercise'},
                {'complexity': {'$gte': float(min_complexity)}},
                {'complexity': {'$lte': float(max_complexity)}}
            ]
        }
        
        results = self.collection.get(
            where=where,
            limit=top_k
        )
        
        exercises = []
        for i, (doc_id, doc, metadata) in enumerate(zip(
            results['ids'],
            results['documents'],
            results['metadatas']
        )):
            exercises.append({
                'id': doc_id,
                'content': doc,
                'metadata': metadata
            })
        
        logger.info(f"Recuperados {len(exercises)} ejercicios por complejidad")
        return exercises
    
    def hybrid_search(self, query: str, metadata_filters: Dict = None,
                     top_k: int = 5) -> List[Dict]:
        """
        Búsqueda híbrida: semántica + filtros de metadatos.
        
        Args:
            query: Consulta de texto
            metadata_filters: Filtros de metadatos (ej: {'type': 'exercise'})
            top_k: Número de resultados
            
        Returns:
            Lista de resultados
        """
        query_embedding = self._generate_query_embedding(query)
        
        where = metadata_filters or {}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where if where else None
        )
        
        hybrid_results = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for doc_id, doc, metadata, distance in zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                hybrid_results.append({
                    'id': doc_id,
                    'content': doc,
                    'metadata': metadata,
                    'similarity': 1 - distance
                })
        
        return hybrid_results

