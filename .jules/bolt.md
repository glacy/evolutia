## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-22 - O(N*M) to O(N) Match Loops Lookup
**Learning:** Nested loops checking for `item1.id == item2.id` (such as searching solutions for exercises) become major bottlenecks during bulk processing (O(N*M) complexity).
**Action:** Always refactor these O(N*M) search loops into O(N) hash map lookups by pre-computing a dictionary mapped by the shared key (e.g., `lookup_dict = {item.id: item for item in items}`). When there is a risk of duplicate keys and the original loop used `break` (first match semantics), populate the dictionary manually with `if key not in dict: dict[key] = item`.
