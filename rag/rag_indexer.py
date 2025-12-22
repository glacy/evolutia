"""
RAG Indexer: Indexa materiales didácticos en un vector store.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class RAGIndexer:
    """Indexa materiales didácticos en un vector store."""
    
    def __init__(self, config: Dict[str, Any], base_path: Path, chroma_client=None):
        """
        Inicializa el indexador.
        
        Args:
            config: Configuración de RAG desde config.yaml
            base_path: Ruta base del proyecto
            chroma_client: Cliente ChromaDB compartido (opcional)
        """
        self.config = config
        self.base_path = Path(base_path)
        self.vector_store = None
        self.embedding_model = None
        self.embedding_provider = config.get('embeddings', {}).get('provider', 'openai')
        self.chroma_client = chroma_client
        self._setup_embeddings()
        self._setup_vector_store()
    
    def _setup_embeddings(self):
        """Configura el modelo de embeddings."""
        embeddings_config = self.config.get('embeddings', {})
        provider = embeddings_config.get('provider', 'openai')
        model_name = embeddings_config.get('model', 'text-embedding-3-small')
        
        if provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("openai no está instalado. Instala con: pip install openai")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY no encontrada en variables de entorno")
            
            self.embedding_client = OpenAI(api_key=api_key)
            self.embedding_model_name = model_name
            logger.info(f"Usando embeddings de OpenAI: {model_name}")
        
        elif provider == 'sentence-transformers':
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("sentence-transformers no está instalado. Instala con: pip install sentence-transformers")
            
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Usando embeddings locales: {model_name}")
        else:
            raise ValueError(f"Proveedor de embeddings no soportado: {provider}")
    
    def _setup_vector_store(self):
        """Configura el vector store."""
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb no está instalado. Instala con: pip install chromadb")
        
        vs_config = self.config.get('vector_store', {})
        persist_dir = Path(vs_config.get('persist_directory', './storage/vector_store'))
        collection_name = vs_config.get('collection_name', 'ejercicios_mmfi')
        
        # Crear directorio si no existe
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Usar cliente compartido si está disponible, sino crear uno nuevo
        if self.chroma_client is not None:
            self.client = self.chroma_client
        else:
            # Inicializar ChromaDB
            self.client = chromadb.PersistentClient(
                path=str(persist_dir.resolve()),
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Obtener o crear colección
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Colección existente cargada: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Nueva colección creada: {collection_name}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding para un texto.
        
        Args:
            text: Texto a convertir en embedding
            
        Returns:
            Lista de floats representando el embedding
        """
        if self.embedding_provider == 'openai':
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model_name,
                input=text
            )
            return response.data[0].embedding
        
        elif self.embedding_provider == 'sentence-transformers':
            return self.embedding_model.encode(text, show_progress_bar=False).tolist()
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos en batch.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de embeddings
        """
        if self.embedding_provider == 'openai':
            batch_size = self.config.get('embeddings', {}).get('batch_size', 100)
            embeddings = []
            
            # Filtrar textos vacíos para evitar error 400 de OpenAI
            valid_texts = [t for t in texts if t and t.strip()]
            if not valid_texts:
                return []
                
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]
                try:
                    response = self.embedding_client.embeddings.create(
                        model=self.embedding_model_name,
                        input=batch
                    )
                    embeddings.extend([item.embedding for item in response.data])
                except Exception as e:
                    logger.error(f"Error en OpenAI embeddings: {e}")
                    logger.error(f"Batch problemático: {batch}")
                    raise
            
            return embeddings
        
        elif self.embedding_provider == 'sentence-transformers':
            return self.embedding_model.encode(texts, show_progress_bar=True, batch_size=32).tolist()
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Divide un texto en chunks con overlap.
        
        Args:
            text: Texto a dividir
            chunk_size: Tamaño de cada chunk (en caracteres aproximados)
            overlap: Overlap entre chunks
            
        Returns:
            Lista de chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Intentar cortar en un punto razonable (espacio o salto de línea)
            if end < len(text):
                last_newline = chunk.rfind('\n')
                last_space = chunk.rfind(' ')
                cut_point = max(last_newline, last_space)
                
                if cut_point > chunk_size * 0.5:  # Si encontramos un buen punto de corte
                    chunk = chunk[:cut_point]
                    end = start + cut_point
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def _create_chunk_id(self, source: str, chunk_index: int) -> str:
        """Crea un ID único para un chunk."""
        content = f"{source}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def index_exercise(self, exercise: Dict, analysis: Dict, metadata: Dict = None) -> List[str]:
        """
        Indexa un ejercicio en el vector store.
        
        Args:
            exercise: Información del ejercicio
            analysis: Análisis de complejidad
            metadata: Metadatos adicionales
            
        Returns:
            Lista de IDs de chunks creados
        """
        content = exercise.get('content', '')
        solution = exercise.get('solution', '')
        
        # Combinar ejercicio y solución
        full_text = f"EJERCICIO:\n{content}\n\n"
        if solution:
            full_text += f"SOLUCIÓN:\n{solution}\n"
        
        # Para ejercicios, usar un solo chunk (son relativamente cortos)
        chunks = [full_text] if len(full_text) < 2000 else self._chunk_text(full_text)
        
        # Preparar metadatos
        chunk_metadata = {
            'type': 'exercise',
            'exercise_type': analysis.get('type', 'desconocido'),
            'complexity': str(analysis.get('total_complexity', 0)),
            'num_variables': str(analysis.get('num_variables', 0)),
            'num_concepts': str(analysis.get('num_concepts', 0)),
            'concepts': ','.join(analysis.get('concepts', [])),
            'source_file': str(exercise.get('source_file', '')),
            'label': exercise.get('label', ''),
        }
        
        if metadata:
            chunk_metadata.update(metadata)
        
        # Generar embeddings
        embeddings = self._generate_embeddings_batch(chunks)
        
        # Sincronizar chunks con embeddings (por si se filtraron vacíos en _generate_embeddings_batch)
        # Aunque aquí preferimos filtrar antes para mantener consistencia
        valid_indices = [i for i, chunk in enumerate(chunks) if chunk and chunk.strip()]
        chunks = [chunks[i] for i in valid_indices]
        
        if not chunks:
            logger.warning(f"Ejercicio {exercise.get('label', 'unknown')} no tiene contenido válido para indexar")
            return []

        # Crear IDs y documentos
        chunk_ids = []
        documents = []
        metadatas = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = self._create_chunk_id(f"{exercise.get('label', 'exercise')}_{i}", i)
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({**chunk_metadata, 'chunk_index': str(i)})
        
        # Agregar a la colección
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Indexado ejercicio {exercise.get('label', 'unknown')}: {len(chunks)} chunks")
        return chunk_ids
    
    def index_reading(self, content: str, metadata: Dict) -> List[str]:
        """
        Indexa una lectura en el vector store.
        
        Args:
            content: Contenido de la lectura
            metadata: Metadatos (tema, título, etc.)
            
        Returns:
            Lista de IDs de chunks creados
        """
        chunking_config = self.config.get('chunking', {})
        chunk_size = chunking_config.get('chunk_size', 1000)
        chunk_overlap = chunking_config.get('chunk_overlap', 100)
        
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)
        
        # Preparar metadatos
        chunk_metadata = {
            'type': 'reading',
            **metadata
        }
        
        # Generar embeddings
        embeddings = self._generate_embeddings_batch(chunks)
        
        # Sincronizar chunks con embeddings
        valid_indices = [i for i, chunk in enumerate(chunks) if chunk and chunk.strip()]
        chunks = [chunks[i] for i in valid_indices]
        
        if not chunks:
            logger.warning(f"Lectura {metadata.get('title', 'unknown')} no tiene contenido válido para indexar")
            return []

        # Crear IDs y documentos
        chunk_ids = []
        documents = []
        metadatas = []
        
        source = metadata.get('source_file', 'reading')
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = self._create_chunk_id(f"{source}_{i}", i)
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({**chunk_metadata, 'chunk_index': str(i)})
        
        # Agregar a la colección
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Indexada lectura {metadata.get('title', 'unknown')}: {len(chunks)} chunks")
        return chunk_ids
    
    def index_materials(self, materials: List[Dict], analyzer) -> Dict[str, int]:
        """
        Indexa una lista de materiales.
        
        Args:
            materials: Lista de materiales extraídos
            analyzer: ExerciseAnalyzer para analizar ejercicios
            
        Returns:
            Diccionario con estadísticas de indexación
        """
        stats = {
            'exercises': 0,
            'readings': 0,
            'chunks': 0
        }
        
        for material in materials:
            # Indexar ejercicios
            exercises = material.get('exercises', [])
            for exercise_data in exercises:
                # Buscar solución correspondiente
                solution = None
                for sol in material.get('solutions', []):
                    if sol['exercise_label'] == exercise_data['label']:
                        solution = sol
                        break
                
                exercise = {
                    'label': exercise_data['label'],
                    'content': exercise_data.get('resolved_content', ''),
                    'source_file': material['file_path'],
                    'solution': solution['resolved_content'] if solution else None
                }
                
                # Analizar ejercicio
                analysis = analyzer.analyze(exercise)
                
                # Indexar
                metadata = {
                    'topic': material.get('frontmatter', {}).get('subject', ''),
                    'file_path': str(material['file_path'])
                }
                
                chunk_ids = self.index_exercise(exercise, analysis, metadata)
                stats['exercises'] += 1
                stats['chunks'] += len(chunk_ids)
            
            # Indexar lecturas (si hay contenido de lectura)
            content_body = material.get('content_body', '')
            filename = str(material.get('file_path', ''))
            
            # Heurística: Indexar como lectura si tiene "lectura" o "teoria" en el nombre 
            # y tiene contenido sustancial (> 200 chars)
            if ('lectura' in filename.lower() or 'teoria' in filename.lower()) and len(content_body) > 200:
                metadata = {
                    'title': material.get('frontmatter', {}).get('title', ''),
                    'subject': material.get('frontmatter', {}).get('subject', ''),
                    'tags': ','.join(material.get('frontmatter', {}).get('tags', [])),
                    'source_file': filename
                }
                chunk_ids = self.index_reading(content_body, metadata)
                stats['readings'] += 1
                stats['chunks'] += len(chunk_ids)
        
        logger.info(f"Indexación completada: {stats}")
        return stats
    
    def clear_collection(self):
        """Limpia la colección (útil para re-indexar)."""
        collection_name = self.collection.name
        self.client.delete_collection(name=collection_name)
        vs_config = self.config.get('vector_store', {})
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Colección {collection_name} limpiada")

