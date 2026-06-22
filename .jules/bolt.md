## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-06-22 - O(N*M) loop optimizations require care to preserve first-match break behavior
**Learning:** When refactoring O(N*M) nested loops to O(N) map lookups, specifically where the inner loop used `break` to capture the *first* match (like in `MaterialExtractor` and `RAGIndexer` when matching exercises to solutions), standard dictionary comprehensions fail because they map to the *last* item if duplicate keys exist.
**Action:** When implementing O(N) map optimizations for first-match loops, populate the dictionary manually with an explicit `if key not in dict:` check to preserve the original `break` behavior correctly.
