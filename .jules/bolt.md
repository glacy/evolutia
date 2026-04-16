## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2024-05-24 - O(N*M) Dictionary Lookup Optimization
**Learning:** In matching relationships like exercises to solutions based on common keys (e.g. `label`), nested O(N*M) search loops with `break` conditions drastically affect performance at scale.
**Action:** Always replace O(N*M) nested search loops with pre-computed O(N) hash map dictionaries for rapid lookups. When preserving a `break` (first-match) behavior, construct the dictionary by only assigning the value if the key `not in dict`.
