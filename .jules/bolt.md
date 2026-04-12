## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-25 - O(N*M) Loop Refactoring to Hash Map Lookups
**Learning:** Nested loops checking `if A == B: break` can become severe performance bottlenecks as the application scales. In Python, constructing an intermediate dictionary `lookup = {item['key']: item for item in list}` converts O(N*M) search time to O(N + M).
**Insight:** Be aware that a simple dictionary comprehension uses "last match wins" if there are duplicates. If the original loop relied on a `break` statement to achieve "first match wins", the dictionary must be populated conditionally: `if key not in lookup: lookup[key] = item`.
**Action:** When performing cross-matching operations between lists (like matching exercises to their solutions), default to creating an O(1) lookup dictionary first instead of using a nested O(N) search loop. Ensure the insertion logic matches the expected duplicate-handling behavior.
