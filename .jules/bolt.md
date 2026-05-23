## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.
## 2025-02-28 - [Dictionary Lookup Optimization]
**Learning:** Replaced O(N*M) nested loops with O(N) lookup dictionaries when matching exercises with solutions in `MaterialExtractor` and `RAGIndexer`. This is a classic pattern in data processing that yields dramatic performance improvements (e.g., 90x+ speedup in synthetic tests for 10k items) while remaining safe and readable.
**Action:** When searching for matches between two lists, pre-compute a lookup dictionary by key to avoid nested loop performance penalties. To preserve the first-match behavior of original `break` statements, populate the dictionary checking `if key not in dict:`.
