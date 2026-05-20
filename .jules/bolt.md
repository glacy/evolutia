## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2024-05-18 - Replacing O(N*M) nested loops with O(N) map lookups
**Learning:** O(N*M) search loops across lists of exercises and solutions present a significant scaling bottleneck. While typical use cases may not feel slow with few materials, using large batches of files creates exponential time complexity. Refactoring logic into O(N) lookup maps is safer when duplicates exist in the mapped collection. A straight dict comprehension maps the *last* matched item if duplicates exist. Since the original implementation used `break` inside the nested loop (preserving the *first* matching solution), the solution must manually check `if key not in dict` to maintain precise functional parity.
**Action:** Always verify `break` vs. `continue` logic when refactoring O(N*M) loop searches into dictionary lookups. For `break` equivalents, ensure the first item mapping is populated and preserved by using explicit `not in` checks rather than list comprehensions, preserving behavioral equivalency with minimal performance overhead.
