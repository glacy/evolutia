## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.
## 2025-05-24 - O(N*M) Loop to O(N) Dictionary Lookup Refactor
**Learning:** Nested loops (O(N*M)) for mapping relational data (like exercises to their solutions) can be a significant performance bottleneck. Refactoring to build a pre-computed dictionary (hash map) reduces the time complexity to O(N), yielding order-of-magnitude speedups for large data sets. However, when simulating the behavior of a `break` statement in the original loop, a naive dictionary comprehension will map the *last* matching item.
**Action:** When refactoring search loops with a `break` to dictionary lookups, populate the dictionary manually and check `if key not in dict:` to preserve the *first-match* behavior safely.
