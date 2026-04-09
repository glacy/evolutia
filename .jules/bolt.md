## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.
## 2024-04-09 - O(N*M) Dictionary Lookup Optimization
**Learning:** Found multiple instances of O(N*M) nested loops used for matching items (exercises to solutions) across the codebase. Refactoring these to O(N) pre-computed dictionary lookups provides a >3x speedup on typical data sizes.
**Action:** Always check for nested iterations where the inner loop's purpose is simply finding a matching related entity. Pre-compute lookups instead. When refactoring an inner loop that uses `break` to find the *first* match, populate the pre-computed dictionary safely by checking `if key not in dict:` to preserve the exact semantics.
