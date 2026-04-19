## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-23 - Optimizing Python re.finditer loops
**Learning:** Sequential `or` evaluations on `match.group('name')` (e.g. `match.group('name1') or match.group('name2')`) inside a `re.finditer` loop introduce unnecessary Python evaluation overhead.
**Insight:** `match.lastgroup` contains the name of the last matched capturing group.
**Action:** Replace sequential `or` clauses with a direct lookup `match.group(match.lastgroup)` for complex regex alternations with named groups to improve performance and code maintainability.
