## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-24 - Optimizing O(N*M) Loops to O(N) Lookups
**Learning:** Refactoring nested search loops into dictionary lookups requires preserving first-match semantics. A naive dictionary comprehension overwrites earlier keys with later ones. To perfectly match the behavior of a `break` statement in a loop, the lookup dictionary must be populated manually with if key not in map checks.
**Action:** When migrating from O(N*M) searches to O(N) dictionary maps, always verify whether duplicate keys can exist and whether the original code intended to take the first or last match.
