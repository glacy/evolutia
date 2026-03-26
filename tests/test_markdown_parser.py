
from evolutia.utils.markdown_parser import (
    extract_frontmatter,
    extract_exercise_blocks,
    extract_solution_blocks
)

def test_extract_frontmatter():
    content = """---
title: Test Page
author: Bolt
---

# Header
Some content here.
"""
    frontmatter, body = extract_frontmatter(content)
    assert frontmatter['title'] == 'Test Page'
    assert frontmatter['author'] == 'Bolt'
    assert body.strip() == "# Header\nSome content here."

def test_extract_exercise_blocks():
    content = """
Some text before.

```{exercise}
:label: ex1-01
This is the exercise content.
```

More text.

````{exercise}
:label: ex1-02
Another exercise with `code` block inside.
````
"""
    exercises = extract_exercise_blocks(content)
    assert len(exercises) == 2
    assert exercises[0]['label'] == 'ex1-01'
    assert exercises[0]['content'] == 'This is the exercise content.'
    assert exercises[1]['label'] == 'ex1-02'
    assert exercises[1]['content'] == 'Another exercise with `code` block inside.'

def test_extract_solution_blocks():
    content = """
Some text.

```{solution} ex1-01
:label: sol-ex1-01
This is the solution content.
```

````{solution} ex1-02
:label: sol-ex1-02
Solution with math $x=y$.
````
"""
    solutions = extract_solution_blocks(content)
    assert len(solutions) == 2
    assert solutions[0]['exercise_label'] == 'ex1-01'
    assert solutions[0]['label'] == 'sol-ex1-01'
    assert solutions[0]['content'] == 'This is the solution content.'

    assert solutions[1]['exercise_label'] == 'ex1-02'
    assert solutions[1]['label'] == 'sol-ex1-02'
    assert solutions[1]['content'] == 'Solution with math $x=y$.'

def test_extract_exercise_with_include():
    content = """
````{exercise}
:label: ex-include
```{include} ./path/to/exercise.md
```
````
"""
    exercises = extract_exercise_blocks(content)
    assert len(exercises) == 1
    assert exercises[0]['type'] == 'include'
    assert exercises[0]['include_path'] == './path/to/exercise.md'

def test_extract_solution_with_include():
    content = """
````{solution} ex-include
:label: sol-include
```{include} ./path/to/solution.md
```
````
"""
    solutions = extract_solution_blocks(content)
    assert len(solutions) == 1
    assert len(solutions[0]['include_paths']) == 1
    assert solutions[0]['include_paths'][0] == './path/to/solution.md'
