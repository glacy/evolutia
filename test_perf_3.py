import re
import time

EXERCISE_PATTERN = re.compile(r'(`{3,4})\{exercise\}(?:\s+\d+)?\s*\n:label:\s+(\S+)\s*\n(.*?)(?=\1)', re.DOTALL)

content = """
```{exercise} 1
:label: ex1-01
This is an exercise with $x^2$.
```
""" * 1000

def test_original():
    start = time.time()
    for _ in range(100):
        exercises = []
        matches = EXERCISE_PATTERN.finditer(content)
        for match in matches:
            label = match.group(2)
            exercise_content = match.group(3).strip()
            exercises.append({
                'label': label,
                'content': exercise_content,
                'include_path': None,
                'type': 'inline'
            })
    return time.time() - start

def test_optimized():
    start = time.time()
    for _ in range(100):
        exercises = []
        matches = EXERCISE_PATTERN.finditer(content)
        for match in matches:
            label = match[2]
            exercise_content = match[3].strip()
            exercises.append({
                'label': label,
                'content': exercise_content,
                'include_path': None,
                'type': 'inline'
            })
    return time.time() - start

print(f"Original: {test_original():.4f}s")
print(f"Optimized: {test_optimized():.4f}s")
