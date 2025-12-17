"""
RAG Manager: Orquesta indexación y recuperación del sistema RAG.
"""
import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, Any, List

try:
    from rag.rag_indexer import RAGIndexer
    from rag.rag_retriever import RAGRetriever
except ImportError:
    try:
        from .rag_indexer import RAGIndexer
        from .rag_retriever import RAGRetriever
    except ImportError:
        from rag_indexer import RAGIndexer
        from rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)


class RAGManager:
    """Gestiona el sistema RAG completo."""
    
    def __init__(self, config_path: Optional[Path] = None, base_path: Optional[Path] = None):
        """
        Inicializa el gestor RAG.
        
        Args:
            config_path: Ruta al archivo de configuración
            base_path: Ruta base del proyecto
        """
        self.config = self._load_config(config_path)
        self.base_path = Path(base_path) if base_path else Path('.')
        self.indexer = None
        self.retriever = None
        self._initialized = False
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Carga la configuración de RAG."""
        if config_path is None:
            # Intentar buscar en root, luego default interno
            import sys
            # Si estamos en un paquete o script, buscar relativo
            script_dir = Path(__file__).parent.parent
            root_config = script_dir.parent / 'evolutia_config.yaml'
            if root_config.exists():
                config_path = root_config
            else:
               config_path = script_dir / 'config' / 'config.yaml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('rag', {})
        except Exception as e:
            logger.warning(f"No se pudo cargar configuración RAG: {e}. Usando valores por defecto.")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto."""
        return {
            'vector_store': {
                'type': 'chromadb',
                'persist_directory': './storage/vector_store',
                'collection_name': 'ejercicios_mmfi'
            },
            'embeddings': {
                'provider': 'openai',
                'model': 'text-embedding-3-small',
                'batch_size': 100
            },
            'retrieval': {
                'top_k': 5,
                'similarity_threshold': 0.7,
                'use_metadata_filters': True
            },
            'chunking': {
                'chunk_size': 1000,
                'chunk_overlap': 100
            }
        }
    
    def initialize(self, force_reindex: bool = False):
        """
        Inicializa el sistema RAG.
        
        Args:
            force_reindex: Si True, fuerza re-indexación incluso si ya existe
        """
        if self._initialized and not force_reindex:
            return
        
        try:
            # Crear un cliente ChromaDB compartido
            vs_config = self.config.get('vector_store', {})
            persist_dir = Path(vs_config.get('persist_directory', './storage/vector_store'))
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                import chromadb
                from chromadb.config import Settings
                self.chroma_client = chromadb.PersistentClient(
                    path=str(persist_dir.resolve()),
                    settings=Settings(anonymized_telemetry=False)
                )
            except Exception as e:
                logger.warning(f"No se pudo crear cliente ChromaDB compartido: {e}")
                self.chroma_client = None
            
            # Inicializar indexer con cliente compartido
            self.indexer = RAGIndexer(self.config, self.base_path, chroma_client=self.chroma_client)
            
            # Inicializar retriever con cliente compartido
            self.retriever = RAGRetriever(self.config, self.base_path, chroma_client=self.chroma_client)
            
            self._initialized = True
            logger.info("Sistema RAG inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando RAG: {e}")
            raise
    
    def index_materials(self, materials: List[Dict], analyzer, clear_existing: bool = False) -> Dict[str, int]:
        """
        Indexa materiales en el vector store.
        
        Args:
            materials: Lista de materiales extraídos
            analyzer: ExerciseAnalyzer para analizar ejercicios
            clear_existing: Si True, limpia la colección antes de indexar
            
        Returns:
            Estadísticas de indexación
        """
        if not self._initialized:
            self.initialize()
        
        if clear_existing:
            logger.info("Limpiando colección existente...")
            self.indexer.clear_collection()
            # Actualizar la colección en el retriever si existe, ya que ha sido recreada
            if self.retriever and self.indexer.collection:
                self.retriever.collection = self.indexer.collection
                logger.info("Referencia de colección actualizada en retriever")
        
        logger.info(f"Indexando {len(materials)} materiales...")
        stats = self.indexer.index_materials(materials, analyzer)
        
        logger.info(f"Indexación completada: {stats}")
        return stats
    
    def get_retriever(self) -> Optional[RAGRetriever]:
        """
        Obtiene el retriever inicializado.
        
        Returns:
            Instancia de RAGRetriever o None si no está inicializado
        """
        if not self._initialized:
            self.initialize()
        
        return self.retriever
    
    def get_indexer(self) -> Optional[RAGIndexer]:
        """
        Obtiene el indexer inicializado.
        
        Returns:
            Instancia de RAGIndexer o None si no está inicializado
        """
        if not self._initialized:
            self.initialize()
        
        return self.indexer
    
    def is_indexed(self) -> bool:
        """
        Verifica si el vector store tiene contenido indexado.
        
        Returns:
            True si hay contenido indexado
        """
        try:
            if not self._initialized:
                self.initialize()
            
            # Intentar obtener el conteo de la colección
            count = self.indexer.collection.count()
            return count > 0
        except Exception as e:
            logger.warning(f"Error verificando índice: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            if not self._initialized:
                self.initialize()
            
            count = self.indexer.collection.count()
            
            # Obtener muestra de metadatos para estadísticas
            sample = self.indexer.collection.get(limit=100)
            
            exercises = sum(1 for m in sample.get('metadatas', []) if m.get('type') == 'exercise')
            readings = sum(1 for m in sample.get('metadatas', []) if m.get('type') == 'reading')
            
            return {
                'total_chunks': count,
                'estimated_exercises': exercises,
                'estimated_readings': readings,
                'collection_name': self.indexer.collection.name
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'error': str(e)}

