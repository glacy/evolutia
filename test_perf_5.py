import re
import time

COMBINED_MATH_PATTERN = re.compile(
    r':::\{math\}\s*(?P<block_content>.*?)\s*:::|'
    r'\$\$(?P<display_dollar>[^$]+)\$\$|\\\[(?P<display_bracket>[^\]]+)\\\]|'
    r'\$(?P<inline_dollar>[^$]+)\$|\\\((?P<inline_paren>[^\)]+)\\\)',
    re.DOTALL
)

content = """
Here is some math: $x^2 + y^2 = z^2$
And a block:
:::{math}
\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
:::
More display math: $$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$
Bracket: \\[ F = ma \\]
Paren: \\( E = mc^2 \\)
""" * 1000

def test_original():
    start = time.time()
    for _ in range(100):
        expressions = []
        for match in COMBINED_MATH_PATTERN.finditer(content):
            expr = (
                match.group('block_content') or
                match.group('display_dollar') or
                match.group('display_bracket') or
                match.group('inline_dollar') or
                match.group('inline_paren')
            )
            if expr:
                expressions.append(expr.strip())
    return time.time() - start

def test_optimized():
    start = time.time()
    for _ in range(100):
        expressions = []
        for match in COMBINED_MATH_PATTERN.finditer(content):
            expr = match.group(match.lastgroup)
            if expr:
                expressions.append(expr.strip())
    return time.time() - start

print(f"Original: {test_original():.4f}s")
print(f"Optimized: {test_optimized():.4f}s")
