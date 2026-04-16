import sys
import os

# mock dependencies
os.makedirs("mocks", exist_ok=True)
with open("mocks/tqdm.py", "w") as f:
    f.write("def tqdm(iterable, *args, **kwargs):\n    return iterable\n")
with open("mocks/yaml.py", "w") as f:
    f.write("def safe_load(*args, **kwargs):\n    return {}\n")
with open("mocks/dotenv.py", "w") as f:
    f.write("def load_dotenv(*args, **kwargs):\n    return True\n")

sys.path.insert(0, os.path.abspath("mocks"))

import time
from evolutia.material_extractor import MaterialExtractor

# mock setup
extractor = MaterialExtractor(".")

materials = []
for i in range(10): # 10 materials
    exercises = [{'label': f'ex_{j}', 'content': 'cont', 'resolved_content': 'cont'} for j in range(1000)]
    solutions = [{'exercise_label': f'ex_{j}', 'label': f'sol_{j}', 'content': 'cont', 'resolved_content': 'cont'} for j in range(1000)]

    materials.append({
        'exercises': exercises,
        'solutions': solutions,
        'file_path': 'foo.md',
        'frontmatter': {}
    })

start = time.time()
res = extractor.get_all_exercises(materials)
end = time.time()
print(f"Original time taken: {end - start:.4f} seconds")

class FastExtractor(MaterialExtractor):
    def get_all_exercises(self, materials):
        all_exercises = []
        for material in materials:
            # O(N) dict lookup
            solutions_by_label = {}
            for sol in material['solutions']:
                if sol['exercise_label'] not in solutions_by_label:
                    solutions_by_label[sol['exercise_label']] = sol

            for exercise in material['exercises']:
                solution = solutions_by_label.get(exercise['label'])
                exercise_data = {
                    'label': exercise['label'],
                    'content': exercise['resolved_content'],
                    'source_file': material['file_path'],
                    'frontmatter': material['frontmatter'],
                    'solution': solution['resolved_content'] if solution else None,
                    'solution_label': solution['label'] if solution else None
                }
                all_exercises.append(exercise_data)
        return all_exercises

fast_extractor = FastExtractor(".")
start = time.time()
res_fast = fast_extractor.get_all_exercises(materials)
end = time.time()
print(f"Optimized time taken: {end - start:.4f} seconds")

# Verify equality
assert len(res) == len(res_fast)
assert res == res_fast

# clean up
os.remove("mocks/tqdm.py")
os.remove("mocks/yaml.py")
os.remove("mocks/dotenv.py")
import shutil
shutil.rmtree("mocks")
