import re
import time

COMBINED_MATH_PATTERN = re.compile(
    r':::\{math\}\s*(?P<block_content>.*?)\s*:::|'
    r'\$\$(?P<display_dollar>[^$]+)\$\$|\\\[(?P<display_bracket>[^\]]+)\\\]|'
    r'\$(?P<inline_dollar>[^$]+)\$|\\\((?P<inline_paren>[^\)]+)\\\)',
    re.DOTALL
)

print(COMBINED_MATH_PATTERN.search('$$\\sum_{i=1}^n i$$').lastgroup)
