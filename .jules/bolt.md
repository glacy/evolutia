## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-20 - Preserving Loop Control Semantics with Map Lookups
**Learning:** Refactoring O(N*M) nested search loops (which stop on the first match via a `break` statement) into O(N) hash map lookups requires care. A standard dictionary comprehension mapping lists to dictionaries (e.g., `{item['key']: item for item in list}`) will overwrite earlier keys with later ones, resulting in a last-match behavior.
**Action:** When converting nested loops with a `break` into dictionary lookups, preserve the first-match behavior by manually populating the dictionary and checking for key existence first (`if key not in dict: dict[key] = item`).
