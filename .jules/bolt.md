## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.
## 2024-06-18 - Replacing O(N*M) lookups with O(N) Hash Maps
**Learning:** Found an O(N*M) loop bottleneck when mapping parsed solutions back to parsed exercises. Two identical patterns were used in `MaterialExtractor.get_all_exercises` and `RAGIndexer.index_materials`.
**Action:** When working with relationships across extracted data, always use an O(N) lookup dictionary keyed by a unique identifier (`exercise_label` in this case) rather than nested loops iterating over the entire second list. Use `if key not in lookup:` during construction to preserve the original loop's `break` behavior.
