## 2025-05-15 - Regex Alternation Performance
**Learning:** Replacing multiple `re.search()` calls for simple literals with a single `re.compile(r'literal1|literal2|...')` regex was ~50% SLOWER in Python.
**Insight:** Python's `re` module likely uses optimized string search algorithms (like Boyer-Moore) for simple literal patterns, which are faster than the state machine overhead of a large alternation regex.
**Action:** Prefer multiple simple `re.search()` calls over complex alternations when patterns are mostly literals. Only use combined regex when tokenization/parsing requires strictly ordered matching or when patterns share complex prefixes.

## 2025-05-20 - Pre-compiling Regex in Loops
**Learning:** `re.findall(pattern, string)` recompiles (or retrieves from cache) the pattern on every call. In high-frequency functions called inside loops (like complexity estimation), this overhead adds up.
**Action:** Always pre-compile regexes (`re.compile`) into module-level or class-level constants if they are used repeatedly, especially in tight loops or recursive functions.

## 2025-05-25 - Asyncio loop execution anti-pattern
**Learning:** Calling `loop.run_until_complete()` inside a loop over `asyncio.as_completed()` blocks the event loop on each iteration. This forces tasks that could be handled concurrently to run strictly sequentially, negating the throughput benefits of asynchronous execution.
**Action:** When gathering results from multiple concurrent async tasks, wrap the task loop inside an `async def` function and `await` the results properly. Then call `loop.run_until_complete()` only once on the wrapper function.
