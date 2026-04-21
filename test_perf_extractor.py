import sys
import os
sys.path.insert(0, os.path.abspath('mocks'))

from evolutia.material_extractor import MaterialExtractor
import time
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as d:
    p = Path(d)
    (p / "practicas").mkdir()
    (p / "lecturas").mkdir()
    (p / "tareas" / "t1").mkdir(parents=True)

    for i in range(100):
        with open(p / "practicas" / f"p{i}.md", "w") as f:
            f.write(f"---\ntags: [math, physics]\n---\n# Content {i}")

    extractor = MaterialExtractor(str(p))
    start = time.time()
    for _ in range(10):
        extractor.extract_by_topic("math")
    print(f"Original logic: {time.time() - start:.4f}s")

    # Let's see the logic of extract_by_topic
