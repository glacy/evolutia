## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-23 - O(N) Hash Map Lookup for First Match
**Learning:** When refactoring O(N*M) search loops into O(N) dictionary lookups, a naive dictionary comprehension will map to the *last* matching item. To preserve a `break` statement's *first-match* behavior, populate the dictionary manually checking `if key not in dict:`.
**Action:** Always verify the original loop's behavior (e.g., `break`, `continue`, `return`) and replicate its exact logic when building O(1) lookup structures.
