## 2024-04-13 - Regex Named Groups Optimization
**Learning:** Using `match.group('name1') or match.group('name2') ...` with multiple non-matching alternations in `re.finditer` is significantly slower than using `match.group(match.lastgroup)`.
**Action:** Always prefer `match.lastgroup` to extract the correct captured group in complex combined regexes instead of sequential truthiness checks.

## 2024-04-13 - Batch String Concatenation for RegEx
**Learning:** Running `re.finditer` inside a Python loop over an array of short strings introduces massive overhead.
**Action:** Whenever multiple small strings need to be parsed with the same pattern (e.g., counting or extracting sets), join them via `" ".join()` into a single large block and run `re.finditer` once. This provides up to 20% speedups.
