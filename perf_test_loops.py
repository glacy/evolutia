import time
from evolutia.material_extractor import MaterialExtractor

# Create large mock materials
materials = []
for i in range(10):
    exercises = [{'label': f'ex_{j}', 'content': 'test', 'resolved_content': 'test'} for j in range(1000)]
    solutions = [{'exercise_label': f'ex_{j}', 'label': f'sol_{j}', 'content': 'test', 'resolved_content': 'test'} for j in range(1000)]
    materials.append({
        'file_path': 'test.md',
        'frontmatter': {},
        'exercises': exercises,
        'solutions': solutions
    })

extractor = MaterialExtractor('.')
start = time.time()
for _ in range(10):
    extractor.get_all_exercises(materials)
print(f"O(N*M) time: {time.time() - start:.4f}s")
