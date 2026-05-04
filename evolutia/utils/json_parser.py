"""
Utilidades para parseo robusto de JSON, especialmente útil para respuestas de LLMs
que pueden contener LaTeX o formatos markdown incorrectos.
"""
import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def extract_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Intenta extraer y parsear un objeto JSON de un texto arbitrario.
    Maneja bloques de código markdown y errores comunes de escape en LaTeX.

    Args:
        text: Texto que puede contener JSON (con o sin bloques markdown)

    Returns:
        Diccionario con el JSON parseado o None si falla
    """
    if not text:
        logger.debug("[JsonParser] Texto vacío, retornando None")
        return None

    # 1. Limpieza básica y extracción de bloque de código
    clean_text = text.strip()

    code_block_pattern = re.compile(r'```(?:json)?\s*(.*?)```', re.DOTALL)
    match = code_block_pattern.search(clean_text)

    if match:
        clean_text = match.group(1).strip()
        logger.debug("[JsonParser] Bloque de código JSON detectado y extraído")

    # HEURÍSTICA DE LATEX AGRESIVA
    # En contextos matemáticos, secuencias como \frac, \textbf, \theta son muy comunes.
    # json.loads interpreta \f, \b, \t como caracteres de control (form feed, backspace, tab).
    # Esto corrompe el LaTeX (ej: \theta -> tab + heta).
    # Por lo tanto, aplicamos una limpieza PREVIA al intento de parseo estándar para estas secuencias.

    # Whitelist de escapes que REALMENTE queremos preservar como controles JSON estándar:
    # "  -> \" (comillas dentro de string)
    # \  -> \\ (backslash literal ya escapado)
    # /  -> \/ (forward slash escapado, opcional)
    # n  -> \n (newline - muy común y necesario)
    # r  -> \r (carriage return)
    # u  -> \uXXXX (unicode - aunque \usepackage podría ser problematico, \u requiere 4 hex digits, asi que \usepackage falla json.loads y lo capturamos despues)

    # REMOVIDOS de whitelist (se escaparán a doble backslash):
    # t  -> Para proteger \theta, \textbf, \text, etc.
    # f  -> Para proteger \frac, \forall, etc.
    # b  -> Para proteger \begin, \beta, etc.

    # Regex: Lookbehind negativo para asegurar que no está ya escapado (?<!\\)
    # Lookahead negativo para permitir solo los de whitelist (?!["\\/nru])
    # Así, \t se convierte en \\t (literal \t string), \n se queda como \n (control char).

    regex_latex_fix = r'(?<!\\)\\(?!["\\/nru])'

    try:
        # Aplicar fix agresivo
        fixed_text = re.sub(regex_latex_fix, r'\\\\', clean_text)
        result = json.loads(fixed_text, strict=False)
        logger.info(f"[JsonParser] JSON parseado exitosamente con fix LaTeX (longitud={len(str(result))})")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"[JsonParser] Falló parseo con fix LaTeX: {e}")

    try:
        result = json.loads(clean_text, strict=False)
        logger.info(f"[JsonParser] JSON parseado exitosamente sin fix LaTeX (longitud={len(str(result))})")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"[JsonParser] Fallo parseo JSON sin fix: {e}")

    logger.error(f"[JsonParser] No se pudo parsear JSON. Texto original (inicio): {text[:100]}...")
    return None
