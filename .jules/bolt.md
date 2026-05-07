## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-23 - Reemplazo de O(N*M) a O(N) preservando semántica de break
**Learning:** Reemplazar un loop de búsqueda anidado O(N*M) con un diccionario O(N) puede alterar el comportamiento si hay duplicados. En Python, las comprensiones de diccionario sobrescriben claves, obteniendo el *último* match, mientras que el loop original con `break` obtiene el *primer* match.
**Action:** Al refactorizar loops con `break` hacia diccionarios (como en la asociación de ejercicios con soluciones), poblar el diccionario manualmente verificando `if key not in dict:` para garantizar el comportamiento original (first-match) al tiempo que se reducen las duraciones de procesamiento enormemente en escenarios de carga intensa (ej. 3.8s a 0.07s en benchmarks con 1000 items).
