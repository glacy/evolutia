## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-21 - O(N^2) Nested Array Searches
**Learning:** `evolutia/material_extractor.py` and `evolutia/rag/rag_indexer.py` both relied on O(N*M) nested loops to pair extracted exercises with their corresponding solutions by matching labels across two lists (`material['exercises']` and `material['solutions']`).
**Insight:** In large Markdown files containing hundreds of exercises (common in course materials), iterating through the solutions array for every single exercise blocks thread execution and scales quadratically, becoming a silent performance killer.
**Action:** Always refactor sequential lookup operations between two datasets into an O(N) hash map (dictionary) preprocessing step. Pre-compute `solutions_dict = {sol['label']: sol}` and look up via `.get()`. When replacing a `break` statement with a dictionary, populate it using `if key not in dict:` to preserve first-match behavior.
