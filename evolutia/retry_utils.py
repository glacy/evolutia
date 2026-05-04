"""
Utilidades para manejo de errores y reintentos en EvolutIA.
Incluye decoradores para reintentos automáticos en llamadas a APIs externas.
"""
import asyncio
import functools
import logging
import time
from typing import Type, Tuple, Optional, Callable

logger = logging.getLogger(__name__)


def retry_async(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_backoff: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorador para reintentar funciones asíncronas con backoff exponencial.

    Args:
        max_retries: Número máximo de reintentos (default: 3)
        initial_delay: Retraso inicial en segundos (default: 1.0)
        max_delay: Retraso máximo en segundos (default: 10.0)
        exponential_backoff: Si True, usa backoff exponencial (default: True)
        exceptions: Tupla de excepciones que disparan reintentos (default: all Exception)
        on_retry: Callback opcional que se ejecuta antes de cada reintento

    Example:
        ```python
        @retry_async(max_retries=3, exceptions=(TimeoutError, ConnectionError))
        async def fetch_data(url: str) -> Dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        ```
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"[RetryAsync] Función '{func.__name__}' falló después de "
                            f"{max_retries + 1} intentos. Error: {e}"
                        )
                        raise

                    # Calcular delay con backoff exponencial
                    if exponential_backoff:
                        delay = min(initial_delay * (2 ** attempt), max_delay)
                    else:
                        delay = min(initial_delay + attempt, max_delay)

                    logger.warning(
                        f"[RetryAsync] Intento {attempt + 1}/{max_retries + 1} falló para "
                        f"'{func.__name__}'. Retentando en {delay:.1f}s... Error: {e}"
                    )

                    # Ejecutar callback si está definido
                    if on_retry:
                        await on_retry(attempt + 1, e, *args, **kwargs)

                    # Esperar antes del siguiente intento
                    await asyncio.sleep(delay)

            # Esto nunca debería ejecutarse, pero mypy lo requiere
            raise last_exception if last_exception else RuntimeError("Unexpected error in retry_async")

        return wrapper
    return decorator


def retry_sync(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_backoff: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorador para reintentar funciones síncronas con backoff exponencial.

    Args:
        max_retries: Número máximo de reintentos (default: 3)
        initial_delay: Retraso inicial en segundos (default: 1.0)
        max_delay: Retraso máximo en segundos (default: 10.0)
        exponential_backoff: Si True, usa backoff exponencial (default: True)
        exceptions: Tupla de excepciones que disparan reintentos (default: all Exception)
        on_retry: Callback opcional que se ejecuta antes de cada reintento

    Example:
        ```python
        @retry_sync(max_retries=3, exceptions=(TimeoutError, ConnectionError))
        def fetch_data(url: str) -> Dict:
            response = requests.get(url, timeout=10)
            return response.json()
        ```
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"[RetrySync] Función '{func.__name__}' falló después de "
                            f"{max_retries + 1} intentos. Error: {e}"
                        )
                        raise

                    # Calcular delay con backoff exponencial
                    if exponential_backoff:
                        delay = min(initial_delay * (2 ** attempt), max_delay)
                    else:
                        delay = min(initial_delay + attempt, max_delay)

                    logger.warning(
                        f"[RetrySync] Intento {attempt + 1}/{max_retries + 1} falló para "
                        f"'{func.__name__}'. Retentando en {delay:.1f}s... Error: {e}"
                    )

                    # Ejecutar callback si está definido
                    if on_retry:
                        on_retry(attempt + 1, e, *args, **kwargs)

                    # Esperar antes del siguiente intento
                    time.sleep(delay)

            # Esto nunca debería ejecutarse, pero mypy lo requiere
            raise last_exception if last_exception else RuntimeError("Unexpected error in retry_sync")

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Implementa el patrón Circuit Breaker para evitar llamadas a servicios fallidos.

    Estados: CLOSED (normal), OPEN (fallo), HALF_OPEN (recuperando)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Inicializa el circuit breaker.

        Args:
            failure_threshold: Número de fallos consecutivos para abrir el circuito
            timeout: Tiempo en segundos antes de intentar recuperar (OPEN → HALF_OPEN)
            expected_exception: Tipo de excepción a considerar como fallo
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_allowed(self) -> bool:
        """
        Verifica si se permite ejecutar la operación.

        Returns:
            True si el circuito está cerrado o medio abierto, False si está abierto
        """
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Verificar si es hora de intentar recuperar
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("[CircuitBreaker] Cambiando de OPEN a HALF_OPEN")
                return True
            return False

        if self.state == "HALF_OPEN":
            return True

        return False

    def record_success(self):
        """Registra un éxito exitoso."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("[CircuitBreaker] Cambiando de HALF_OPEN a CLOSED")

        self.failure_count = 0

    def record_failure(self):
        """Registra un fallo."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning(
                    f"[CircuitBreaker] Abriendo circuito después de "
                    f"{self.failure_count} fallos consecutivos"
                )
                self.state = "OPEN"


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """
    Decorador que usa un Circuit Breaker para proteger funciones.

    Args:
        circuit_breaker: Instancia de Circuit Breaker

    Example:
        ```python
        cb = CircuitBreaker(failure_threshold=5, timeout=60.0)

        @with_circuit_breaker(cb)
        async def call_api(url: str) -> Dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        ```
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not circuit_breaker.is_allowed():
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except circuit_breaker.expected_exception:
                circuit_breaker.record_failure()
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not circuit_breaker.is_allowed():
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except circuit_breaker.expected_exception:
                circuit_breaker.record_failure()
                raise

        # Detectar si la función es async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
