## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-25 - Converting O(N*M) Loops to O(N) Dictionary Lookups
**Learning:** When refactoring O(N*M) nested loops that map items (like mapping exercises to solutions) using a `break` statement to find the *first* match, a standard dictionary comprehension (e.g., `{sol['label']: sol for sol in solutions}`) is incorrect because it maps to the *last* matching item if duplicates exist.
**Action:** To preserve exact first-match behavior when converting `break` loops to O(N) hash map lookups, manually populate the dictionary and check for existing keys: `if label not in lookup_dict: lookup_dict[label] = item`.
