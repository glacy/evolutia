## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.
## 2025-05-20 - O(N*M) loop to O(N) dict lookup in MaterialExtractor
**Learning:** In `evolutia/material_extractor.py`, finding the solution for each exercise was using an O(N*M) nested loop. When scaling the number of exercises per material (e.g. from 10 to 500), extraction time jumped significantly due to quadratic complexity.
**Action:** Always replace nested matching loops (especially those matching IDs or labels) with pre-computed O(N) lookup dictionaries. To preserve the original `break` behavior (first match wins), populate the dictionary using `if key not in dict: dict[key] = value`.
