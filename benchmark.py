import time
from typing import List, Dict

def get_all_exercises_original(materials: List[Dict]) -> List[Dict]:
    all_exercises = []
    for material in materials:
        for exercise in material['exercises']:
            solution = None
            for sol in material['solutions']:
                if sol['exercise_label'] == exercise['label']:
                    solution = sol
                    break

            exercise_data = {
                'label': exercise['label'],
                'solution_label': solution['label'] if solution else None
            }
            all_exercises.append(exercise_data)
    return all_exercises

def get_all_exercises_optimized(materials: List[Dict]) -> List[Dict]:
    all_exercises = []
    for material in materials:
        solutions_by_label = {}
        for sol in material['solutions']:
            if sol['exercise_label'] not in solutions_by_label:
                solutions_by_label[sol['exercise_label']] = sol
        for exercise in material['exercises']:
            solution = solutions_by_label.get(exercise['label'])

            exercise_data = {
                'label': exercise['label'],
                'solution_label': solution['label'] if solution else None
            }
            all_exercises.append(exercise_data)
    return all_exercises

# Generate dummy data
materials = []
for i in range(10):
    exercises = [{'label': f'ex_{j}'} for j in range(1000)]
    solutions = [{'exercise_label': f'ex_{j}', 'label': f'sol_{j}'} for j in range(1000)]
    materials.append({'exercises': exercises, 'solutions': solutions})

start = time.time()
get_all_exercises_original(materials)
print(f"Original: {time.time() - start:.4f}s")

start = time.time()
get_all_exercises_optimized(materials)
print(f"Optimized: {time.time() - start:.4f}s")
