## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2024-05-24 - [O(N^2) Loop Optimization in Data Matching]
**Learning:** Matching relationships (like exercises to solutions based on a label) using O(N*M) nested loops becomes a significant bottleneck as dataset sizes grow, particularly in modules like `material_extractor.py` and `rag_indexer.py`.
**Action:** Replace nested loops with an O(N) pre-computed lookup dictionary (hash map) to achieve a 60x speedup in parsing and indexing operations. Use `dict.get()` for O(1) retrieval, while ensuring first-match behavior is preserved by selectively populating the dictionary (`if key not in dict:`).
