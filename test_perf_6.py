import re
import time
from typing import List

LATIN_REGEX = r'\\vec\{([A-Za-z])\}|\\mathbf\{([A-Za-z])\}|\\hat\{([A-Za-z])\}|([A-Za-z])(?![a-z])'
GREEK_REGEX = r'\\(alpha|beta|gamma|delta|epsilon|theta|phi|rho|omega|sigma|lambda|mu|nu|pi|tau)'
COMBINED_VARIABLES_PATTERN = re.compile(f'{LATIN_REGEX}|{GREEK_REGEX}')

expressions = [
    r"\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}",
    r"\alpha + \beta = \gamma",
    r"\vec{A} \cdot \vec{B} = |A| |B| \cos(\theta)",
    r"\sum_{i=1}^n x_i = \mathbf{X}"
] * 1000

def test_original():
    start = time.time()
    for _ in range(100):
        variables = set()
        for expr in expressions:
            for match in COMBINED_VARIABLES_PATTERN.finditer(expr):
                if match.lastindex:
                    var = match.group(match.lastindex)
                    if var:
                        variables.add(var)
    return time.time() - start

def test_optimized():
    start = time.time()
    for _ in range(100):
        variables = set()
        # Batch processing
        combined = " ".join(expressions)
        for match in COMBINED_VARIABLES_PATTERN.finditer(combined):
            if match.lastindex:
                var = match.group(match.lastindex)
                if var:
                    variables.add(var)
    return time.time() - start

print(f"Original: {test_original():.4f}s")
print(f"Optimized: {test_optimized():.4f}s")
