## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-06-29 - O(N*M) Lookup Optimization
**Learning:** Found O(N*M) nested loops searching for corresponding solutions to exercises by label in `MaterialExtractor` and `RAGIndexer`. Refactoring to pre-compute an O(N) hash map reduced processing time from O(N*M) to O(N).
**Action:** When searching for matches across two lists, always pre-compute a dictionary (`{item['key']: item for item in list}`) to achieve O(N) lookup instead of O(N*M) nested loops, especially in data processing or indexing pipelines. Ensure to check `if key not in dict` when populating to preserve `break` (first-match) behavior if duplicates might exist.
