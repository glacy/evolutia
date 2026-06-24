## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-06-24 - O(N*M) loop optimizations in nested lists
**Learning:** Found O(N*M) lookup logic where a solution was searched in a list for every exercise.
**Action:** Replaced nested loops searching by ID/label with a pre-computed dictionary mapping ID -> object (e.g. `solutions_map[label] = sol`), which brings time complexity down from O(N*M) to O(N+M) and provides O(1) lookups. In tests, this yielded ~12x speedup on moderate lists. Preserved first-match behaviour manually `if label not in solutions_map` to prevent subtle bugs.
