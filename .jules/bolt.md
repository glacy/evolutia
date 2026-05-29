## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-06-25 - O(N*M) Loop to O(N) HashMap with First-Match Integrity
**Learning:** Found an O(N*M) bottleneck in `material_extractor.py` and `rag_indexer.py` where the code nested `for sol in solutions` inside `for ex in exercises`. While refactoring to an O(N) hash map is standard, the original loop used a `break` to strictly enforce a "first-match" rule when multiple identical labels existed.
**Insight:** A simple dictionary comprehension (`{sol['label']: sol for sol in solutions}`) overwrites previous keys, mapping to the *last* matching item instead, which breaks the original business logic if there are duplicate labels.
**Action:** When converting O(N*M) search loops with `break` into dictionary lookups, construct the dictionary manually and check `if key not in dict:` to safely preserve first-match behavior while still achieving O(N) performance.
