## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2024-03-05 - [Regex replacement vs. Semantic Code correctness]
**Learning:** While `str.count()` can be faster than `re.findall()` for basic string literals in micro-benchmarks, it breaks functionality when parsing specific semantic patterns (like LaTeX). Replacing regex matching with literal counts in `evolutia/utils/math_extractor.py` introduced functional bugs by capturing unrelated substrings that matched the literal text without word boundaries or context.
**Action:** Never optimize complex string processing routines by replacing compiled regex with simple `str.count()` unless the string pattern is strictly exact and immune to partial sub-string matches. Always prefer algorithmic complexity improvements (like O(N*M) to O(N) Hash map lookups) over micro-optimizing standard library functions.
