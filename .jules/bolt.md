## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-23 - match.lastgroup performance
**Learning:** In python's `re` module, using `match.group(match.lastgroup)` directly is significantly faster than using a chain of python-level boolean evaluations like `match.group('a') or match.group('b') or ...` when iterating with `re.finditer` over regexes with multiple mutually exclusive named capturing groups.
**Action:** When extracting data using complex alternations with named groups in a `finditer` loop, always prefer `match.group(match.lastgroup)` to reduce Python evaluation overhead.

## 2025-05-23 - O(N*M) Dictionary lookups with duplicate keys
**Learning:** When refactoring O(N*M) nested loops into O(N) loops with a dictionary lookup, if the O(N*M) loop used a `break` to capture the first match, the dictionary comprehension will fail to replicate this because it keeps the *last* match for duplicate keys.
**Action:** To correctly translate an O(N*M) first-match loop into an O(N) lookup, populate the dictionary by explicitly checking if the key is already present (`if key not in dict: dict[key] = val`) before relying on it for subsequent `dict.get()` queries.
