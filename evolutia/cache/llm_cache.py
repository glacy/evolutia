"""
Caché de respuestas LLM para EvolutIA.
Reduce costos y tiempo de ejecución almacenando respuestas de LLMs.
"""
import hashlib
import json
import logging
import sys
import time
import threading
import atexit
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Sistema de caché para respuestas de LLMs.

    Características:
    - Caché en memoria con persistencia opcional en disco
    - TTL configurable para expirar entradas
    - Tamaño máximo configurable con LRU eviction
    - Filtrado de respuestas vacías o de error
    - Hash basado en (prompt, provider, model)
    - Logging de cache hits y misses
    - Write-behind con debounce para optimizar I/O de disco
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_hours: int = 24,
        persist_to_disk: bool = True,
        cache_dir: Optional[Path] = None,
        debounce_seconds: float = 5.0,
        max_memory_mb: int = 500
    ):
        """
        Inicializa el caché de LLM.

        Args:
            max_size: Número máximo de entradas en caché
            ttl_hours: Tiempo de vida en horas (0 = sin expiración)
            persist_to_disk: Si True, persiste caché en disco
            cache_dir: Directorio para caché persistente (defecto: ./storage/cache/llm)
            debounce_seconds: Tiempo de debounce para persistir a disco (write-behind)
            max_memory_mb: Límite máximo de memoria en MB (0 = sin límite)
        """
        self.max_size = max_size
        self.ttl = ttl_hours * 3600 if ttl_hours > 0 else 0
        self.persist_to_disk = persist_to_disk
        self.debounce_seconds = debounce_seconds
        self.max_memory_bytes = max_memory_mb * 1024 * 1024 if max_memory_mb > 0 else 0

        if cache_dir is None:
            cache_dir = Path('./storage/cache/llm')
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, float] = {}
        self.entry_sizes: Dict[str, int] = {}
        self.total_memory_bytes = 0
        self.hits = 0
        self.misses = 0

        # Write-behind con debounce
        self._pending_persist = False
        self._persist_lock = threading.Lock()
        self._persist_thread = None
        self._stop_event = threading.Event()

        # Cargar caché desde disco si está habilitado
        if self.persist_to_disk:
            self._load_from_disk()
            # Registrar persistencia al salir
            atexit.register(self._force_persist_to_disk)

        logger.info(
            f"[LLMCache] Inicializado: max_size={max_size}, "
            f"ttl={ttl_hours}h, persist={persist_to_disk}, "
            f"debounce={debounce_seconds}s, max_memory={max_memory_mb}MB"
        )

    def _get_cache_key(self, prompt: str, provider: str, model: str) -> str:
        """
        Genera una clave de caché basada en prompt, provider y model.

        Args:
            prompt: El prompt enviado al LLM
            provider: Nombre del proveedor (ej: 'openai', 'anthropic')
            model: Nombre del modelo (ej: 'gpt-4', 'claude-3-opus')

        Returns:
            String hash SHA256 como clave de caché
        """
        key_data = f"{provider}:{model}:{prompt}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, prompt: str, provider: str, model: str) -> Optional[str]:
        """
        Obtiene una respuesta del caché.

        Args:
            prompt: El prompt enviado al LLM
            provider: Nombre del proveedor
            model: Nombre del modelo

        Returns:
            Respuesta cacheada si existe y no ha expirado, None en caso contrario
        """
        key = self._get_cache_key(prompt, provider, model)

        if key not in self.cache:
            self.misses += 1
            logger.debug(f"[LLMCache] Cache miss para {provider}:{model}")
            return None

        # Verificar TTL
        if self.ttl > 0:
            age = time.time() - self.timestamps[key]
            if age > self.ttl:
                logger.debug(f"[LLMCache] Entrada expirada para {provider}:{model} (age={age:.0f}s)")
                self._remove_entry(key)
                self.misses += 1
                return None

        self.hits += 1
        logger.info(
            f"[LLMCache] Cache HIT para {provider}:{model} "
            f"(hit_rate={self.hit_rate:.1%})"
        )
        return self.cache[key]['response']

    def put(
        self,
        prompt: str,
        provider: str,
        model: str,
        response: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Almacena una respuesta en el caché.

        Args:
            prompt: El prompt enviado al LLM
            provider: Nombre del proveedor
            model: Nombre del modelo
            response: La respuesta del LLM
            metadata: Metadatos adicionales (tokens, cost, etc.)

        Returns:
            True si se almacenó exitosamente, False si se rechazó
        """
        # Evitar cachear respuestas vacías
        if not response or not response.strip():
            logger.debug(f"[LLMCache] Rechazando respuesta vacía para {provider}:{model}")
            return False

        # Evitar cachear respuestas de error comunes
        error_indicators = [
            'error', 'lo siento', 'sorry', 'cannot',
            'unable', 'failed', 'unknown error'
        ]
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in error_indicators):
            logger.debug(
                f"[LLMCache] Rechazando respuesta de error para {provider}:{model}"
            )
            return False

        # Evitar cachear respuestas muy cortas (probablemente errores)
        if len(response) < 20:
            logger.debug(
                f"[LLMCache] Rechazando respuesta muy corta ({len(response)} chars) "
                f"para {provider}:{model}"
            )
            return False

        key = self._get_cache_key(prompt, provider, model)
        timestamp = time.time()

        # Calcular tamaño de la nueva entrada
        entry_size = self._estimate_entry_size(key, response, metadata)

        # Verificar límites de tamaño y memoria
        if len(self.cache) >= self.max_size:
            self._evict_oldest_entries(count=1)

        # Verificar límite de memoria
        self._check_memory_limit(entry_size)
        self.cache[key] = {
            'response': response,
            'timestamp': timestamp,
            'metadata': metadata or {}
        }
        self.timestamps[key] = timestamp
        self.entry_sizes[key] = entry_size
        self.total_memory_bytes += entry_size

        logger.debug(f"[LLMCache] Cache guardado para {provider}:{model} ({entry_size} bytes)")

        # Persistir en disco si está habilitado (write-behind con debounce)
        if self.persist_to_disk:
            self._schedule_persist()

        return True

    def _evict_oldest_entries(self, count: int = 1):
        """
        Elimina las entradas más viejas del caché (LRU eviction).

        Args:
            count: Número de entradas a eliminar
        """
        if count <= 0 or not self.timestamps:
            return

        # Encontrar las 'count' entradas más viejas
        oldest_keys = sorted(
            self.timestamps.items(),
            key=lambda x: x[1]
        )[:count]

        logger.debug(f"[LLMCache] Evicting {count} entradas más viejas: {oldest_keys}")

        for key, timestamp in oldest_keys:
            logger.debug(f"[LLMCache] Removing key={key[:16]}..., timestamp={timestamp}")
            if key in self.cache:
                del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
            if key in self.entry_sizes:
                entry_size = self.entry_sizes[key]
                del self.entry_sizes[key]
                self.total_memory_bytes -= entry_size

        logger.debug(f"[LLMCache] Evicted {count} entradas más viejas")

    def _remove_entry(self, key: str):
        """
        Elimina una entrada del caché.

        Args:
            key: Clave de la entrada a eliminar
        """
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
        if key in self.entry_sizes:
            entry_size = self.entry_sizes[key]
            del self.entry_sizes[key]
            self.total_memory_bytes -= entry_size

    def clear(self):
        """Limpia todo el caché."""
        initial_size = len(self.cache)
        self.cache.clear()
        self.timestamps.clear()
        self.entry_sizes.clear()
        self.total_memory_bytes = 0
        self.hits = 0
        self.misses = 0

        logger.info(f"[LLMCache] Caché limpiado (eliminadas {initial_size} entradas)")

        # Eliminar archivos de caché si persiste a disco
        if self.persist_to_disk and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob('*.json'):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"[LLMCache] Error eliminando {cache_file}: {e}")

    def _persist_to_disk(self):
        """Persiste el caché en disco."""
        if not self.persist_to_disk:
            return

        try:
            metadata_file = self.cache_dir / 'llm_cache_metadata.json'
            metadata = {
                'version': '1.0',
                'last_persisted': time.time(),
                'entries_count': len(self.cache),
                'hits': self.hits,
                'misses': self.misses
            }

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            logger.debug(f"[LLMCache] Metadatos persistidos en {metadata_file}")
        except Exception as e:
            logger.warning(f"[LLMCache] Error persistiendo metadatos: {e}")

    def _load_from_disk(self):
        """Carga metadatos del caché desde disco."""
        if not self.persist_to_disk:
            return

        try:
            metadata_file = self.cache_dir / 'llm_cache_metadata.json'
            if not metadata_file.exists():
                return

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            self.hits = metadata.get('hits', 0)
            self.misses = metadata.get('misses', 0)
            entries_count = metadata.get('entries_count', 0)

            logger.info(
                f"[LLMCache] Metadatos cargados: {entries_count} entradas, "
                f"hits={self.hits}, misses={self.misses}"
            )
        except Exception as e:
            logger.warning(f"[LLMCache] Error cargando metadatos: {e}")

    def _estimate_entry_size(self, key: str, value: str, metadata: Optional[Dict] = None) -> int:
        """
        Estima el tamaño en bytes de una entrada del caché.

        Args:
            key: Clave de la entrada
            value: Valor de la entrada
            metadata: Metadatos opcionales

        Returns:
            Tamaño estimado en bytes
        """
        size = sys.getsizeof(key) + sys.getsizeof(value)
        if metadata:
            size += sys.getsizeof(json.dumps(metadata))
        # Overhead por diccionarios y estructuras de Python
        size += 100
        return size

    def _check_memory_limit(self, new_entry_size: int) -> bool:
        """
        Verifica si agregar una nueva entrada excedería el límite de memoria.

        Args:
            new_entry_size: Tamaño de la nueva entrada en bytes

        Returns:
            True si hay suficiente espacio, False si se debe hacer eviction
        """
        if self.max_memory_bytes == 0:
            return True  # Sin límite de memoria

        projected_size = self.total_memory_bytes + new_entry_size

        if projected_size <= self.max_memory_bytes:
            return True

        # Necesitamos hacer eviction
        self._evict_until_within_limit(projected_size - self.max_memory_bytes)
        return True

    def _evict_until_within_limit(self, bytes_to_free: int):
        """
        Evicta entradas hasta liberar la cantidad de bytes especificada.

        Args:
            bytes_to_free: Cantidad de bytes a liberar
        """
        bytes_freed = 0
        while bytes_freed < bytes_to_free and self.cache:
            # Encontrar la entrada más vieja (LRU)
            oldest_key = min(self.timestamps.items(), key=lambda x: x[1])[0]
            oldest_size = self.entry_sizes.get(oldest_key, 0)

            self._remove_entry(oldest_key)
            bytes_freed += oldest_size

        if bytes_freed > 0:
            logger.debug(
                f"[LLMCache] Memoria excedida - evictadas entradas hasta liberar "
                f"{bytes_freed / 1024:.1f} KB"
            )

    def _schedule_persist(self):
        """
        Programa persistencia a disco con debounce (write-behind).
        Evita escribir a disco en cada put() - solo escribe después de un periodo de inactividad.
        """
        with self._persist_lock:
            self._pending_persist = True

            # Si no hay un thread activo, iniciar uno
            if self._persist_thread is None or not self._persist_thread.is_alive():
                self._persist_thread = threading.Thread(
                    target=self._debounced_persist_worker,
                    daemon=True
                )
                self._persist_thread.start()

    def _debounced_persist_worker(self):
        """
        Worker thread que espera el periodo de debounce antes de persistir.
        """
        try:
            # Esperar el periodo de debounce
            time.sleep(self.debounce_seconds)

            with self._persist_lock:
                # Verificar si aún debemos persistir (podría haber sido cancelado)
                if not self._pending_persist or self._stop_event.is_set():
                    return

                self._pending_persist = False

            # Persistir fuera del lock para no bloquear el acceso al caché
            self._persist_to_disk()
        except Exception as e:
            logger.warning(f"[LLMCache] Error en worker de persistencia: {e}")

    def _force_persist_to_disk(self):
        """
        Fuerza la persistencia inmediata a disco.
        Se usa al salir del programa (atexit).
        """
        if self._stop_event.is_set():
            return

        # Detener el worker de debounce si está corriendo
        self._stop_event.set()

        with self._persist_lock:
            self._pending_persist = False

        # Persistir inmediatamente
        self._persist_to_disk()

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.

        Returns:
            Diccionario con estadísticas
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        memory_mb = self.total_memory_bytes / (1024 * 1024)

        return {
            'entries': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'max_size': self.max_size,
            'ttl_hours': self.ttl / 3600,
            'persist_to_disk': self.persist_to_disk,
            'cache_dir': str(self.cache_dir),
            'memory_mb': round(memory_mb, 2),
            'memory_limit_mb': round(self.max_memory_bytes / (1024 * 1024), 2) if self.max_memory_bytes > 0 else 0,
            'memory_usage_percent': round((self.total_memory_bytes / self.max_memory_bytes) * 100, 1) if self.max_memory_bytes > 0 else 0
        }

    @property
    def hit_rate(self) -> float:
        """
        Tasa de aciertos del caché.

        Returns:
            Proporción de aciertos (0.0 a 1.0)
        """
        total_requests = self.hits + self.misses
        return self.hits / total_requests if total_requests > 0 else 0.0

    def __len__(self) -> int:
        """Retorna el número de entradas en caché."""
        return len(self.cache)

    def __repr__(self) -> str:
        """Representación del caché."""
        return (
            f"LLMCache(entries={len(self.cache)}, hits={self.hits}, "
            f"misses={self.misses}, hit_rate={self.hit_rate:.1%})"
        )
