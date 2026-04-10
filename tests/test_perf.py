import re
from timeit import timeit

COMBINED_MATH_PATTERN = re.compile(
    r':::\{math\}\s*(?P<block_content>.*?)\s*:::|'
    r'\$\$(?P<display_dollar>[^$]+)\$\$|\\\[(?P<display_bracket>[^\]]+)\\\]|'
    r'\$(?P<inline_dollar>[^$]+)\$|\\\((?P<inline_paren>[^\)]+)\\\)',
    re.DOTALL
)

content = r"test $$1+1$$ test \(\sin(x)\) test $$2+2$$ test \(\cos(x)\)" * 100

def old_way():
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
    return expressions

def new_way():
    expressions = []
    for match in COMBINED_MATH_PATTERN.finditer(content):
        if match.lastgroup:
            expr = match.group(match.lastgroup)
            if expr:
                expressions.append(expr.strip())
    return expressions

print("Old:", timeit(old_way, number=1000))
print("New:", timeit(new_way, number=1000))
