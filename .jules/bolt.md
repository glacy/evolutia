## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-06-25 - Replace O(N*M) search loops with Dictionary Lookup
**Learning:** Nested loops to match related objects (e.g., exercises and solutions) scale poorly `O(N*M)` and slow down indexer/extractor pipelines significantly.
**Action:** Always pre-compute a lookup dictionary (`O(N)`) before iterating when matching items across lists, especially in data processing functions. Check `if key not in dict:` to preserve first-match behavior when populating the dictionary.
