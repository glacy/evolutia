## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-02-20 - O(N) Hash Map Lookup for Material-Solution Matching
**Learning:** The application uses an O(N*M) nested loop pattern to match solutions to their corresponding exercises across multiple files (`MaterialExtractor.get_all_exercises` and `RAGIndexer.index_materials`). When scaling to large directories with hundreds of exercises and solutions, this nested matching creates an unnecessary performance bottleneck. Furthermore, `break` statements used in the inner loop require careful attention: a simple dictionary comprehension `{sol['exercise_label']: sol for sol in solutions}` would keep the *last* duplicate match instead of the first.
**Action:** Replaced the O(N*M) search loops with an O(N) dictionary lookup populated manually (`if key not in dict`) to perfectly preserve the original first-match behavior. This provides an ~8.6x speedup on arrays of size 100 while maintaining functional correctness.
