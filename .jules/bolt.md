## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-21 - O(N*M) Loop to Dictionary Lookup Duplicate Semantics
**Learning:** When refactoring O(N*M) search loops that use a `break` statement into O(N) dictionary lookups, a naive dictionary comprehension (e.g., `{item['key']: item for item in list}`) will map to the *last* matching item if duplicates exist. The original `break` loop behavior resolves to the *first* matching item.
**Action:** Always verify if duplicates are possible in the data structure when replacing search loops with dictionary mappings. To maintain "first-match" semantics, populate the dictionary using an explicit loop with a presence check: `if key not in dict: dict[key] = item`.
