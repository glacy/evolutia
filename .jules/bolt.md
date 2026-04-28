## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-22 - Nested Loop to Hash Map Optimization (get_all_exercises)
**Learning:** `get_all_exercises` inside `MaterialExtractor` contained an O(N*M) nested loop checking exercises against solutions, taking ~0.38s for 10,000 matches. Replacing it with an O(N) pre-computed solution dictionary dropped execution time to ~0.01s (a 38x speedup).
**Action:** When mapping nested items (like exercises to solutions) via explicit IDs (like `exercise_label`), always pre-compute a lookup dictionary (`O(1)` access) for the inner list rather than using nested `for` loops with `break` (`O(M)` access).
