## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-22 - Nested List Search Complexity
**Learning:** O(N*M) nested loops to find items by key (like matching exercises to solutions) can become a significant bottleneck as dataset sizes grow. In Python, constructing an intermediate lookup dictionary is extremely fast and scales significantly better, reducing lookup from O(N*M) to O(N).
**Action:** When finding matching items across two lists by a common key, always prefer a pre-computed dictionary (`{item['key']: item for item in list}`) for O(1) lookups instead of nested loops. If there are duplicates and the original code relied on breaking on the first match, construct the dictionary explicitly checking `if key not in dict: dict[key] = item`.
