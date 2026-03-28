## 2024-05-22 - [Regex Optimization Pitfalls]
**Learning:** Optimizing Python regex loops by using `match.lastgroup` instead of sequential `match.group(name)` checks can be unsafe if the regex contains nested capturing groups. `lastgroup` points to the *last closed* capturing group, which might be an inner group, not the top-level named group you expect.
**Action:** Always validate `match.lastgroup` against a set of expected "payload" group names before using it, or ensure the regex uses non-capturing groups `(?:...)` strictly.
