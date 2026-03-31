## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2026-03-31 - Optimize O(N*M) nested loops to O(N) using dictionary lookups
**Learning:** When matching items across two lists (e.g., finding solutions for exercises), nested loops result in O(N*M) time complexity. Using a dictionary to map keys to values reduces this to O(N+M), but one must be careful to preserve 'first-match' behavior if duplicate keys exist by only adding to the dict if the key is not already present.
**Action:** Use pre-computed dictionaries instead of nested loops for lookups. When refactoring loops with a `break` statement, populate the lookup dictionary conditionally (`if key not in dict`) to maintain the first-match logic.
