## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-23 - Optimizing capture group extraction
**Learning:** Using `match.group(match.lastgroup)` is faster than evaluating multiple `or` conditions (like `match.group('a') or match.group('b') or ...`) when extracting matched values from a regex `finditer` loop containing multiple alternative named groups.
**Action:** When extracting alternatives from regex match objects where only one group is expected to match, use `match.group(match.lastgroup)` or `match.lastindex` to access the matched content directly and avoid unnecessary Python evaluation overhead within the parsing loop.
