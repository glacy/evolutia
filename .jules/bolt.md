## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-20 - Optimizing O(N*M) Loops to O(N) Maps
**Learning:** Nested loops checking for conditions like `if item_a.id == item_b.id` combined with `break` lead to O(N*M) time complexity. When migrating these to an O(N) dictionary lookup, a dictionary comprehension (e.g., `{item['key']: item for item in items}`) overrides duplicates, returning the *last* match instead of the *first* match.
**Action:** When converting O(N*M) search loops to O(N) lookup maps, if the original loop utilized a `break` to return the first matching item, ensure the first-match behavior is preserved by manually populating the dictionary: `if key not in mapping: mapping[key] = item`.
