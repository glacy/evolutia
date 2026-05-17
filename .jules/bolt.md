## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.
## 2025-02-23 - [O(1) Dictionary Lookups for Array Matching]
**Learning:** Nested loops iterating over arrays to find matching items (e.g., finding a solution for an exercise by comparing labels) introduce an O(N*M) time complexity bottleneck. In `MaterialExtractor` and `RAGIndexer`, this slowed down processing significantly as materials grew.
**Action:** When matching items between two arrays based on a common key, pre-compute a lookup dictionary (`{item['key']: item}`) for the inner array. This reduces the search to an O(1) dictionary lookup, improving overall time complexity to O(N+M). To preserve original "first-match" behavior from a loop `break`, populate the dictionary safely using `if key not in dict: dict[key] = item`.
