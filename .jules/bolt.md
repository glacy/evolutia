## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-25 - O(N*M) Nested Loop Optimization
**Learning:** Found O(N*M) nested loops matching exercises to their solutions in `MaterialExtractor` and `RAGIndexer`. Refactored to O(N) by building a precomputed hash map (`solutions_map`). Benchmark showed a ~100x-200x speedup for 5000 items. To preserve original `break` (first-match) behavior instead of dictionary last-match behavior, used `if label not in solutions_map:` when populating the hash map.
**Action:** Actively scan large list processing loops for $O(N^2)$ cross-referencing and replace with $O(N)$ dictionary lookups, keeping care to manually handle deduplication/first-match behavior to prevent regressions.
