## 2024-05-18 - [Avoid O(N*M) lookups in data joining]
**Learning:** Matching items (e.g., exercises to solutions) using nested loops creates an O(N*M) bottleneck.
**Action:** Always use an O(N) pre-computed lookup dictionary for such relationships, ensuring first-match behavior if necessary with `if key not in dict: dict[key] = item`.
