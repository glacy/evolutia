import time

materials = [{
    'file_path': 'test.md',
    'frontmatter': {},
    'exercises': [{'label': f'ex_{i}', 'resolved_content': f'content {i}'} for i in range(1000)],
    'solutions': [{'exercise_label': f'ex_{i}', 'label': f'sol_{i}', 'resolved_content': f'sol content {i}'} for i in range(1000)]
}]

start = time.time()
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
            'solution': solution['resolved_content'] if solution else None
        }
        all_exercises.append(exercise_data)
end = time.time()
print(f"O(N*M) loop: {end - start:.4f} seconds")

start = time.time()
all_exercises_opt = []
for material in materials:
    # O(N) optimization
    solutions_by_label = {}
    for sol in material['solutions']:
        if sol['exercise_label'] not in solutions_by_label:
            solutions_by_label[sol['exercise_label']] = sol

    for exercise in material['exercises']:
        solution = solutions_by_label.get(exercise['label'])
        exercise_data = {
            'label': exercise['label'],
            'solution': solution['resolved_content'] if solution else None
        }
        all_exercises_opt.append(exercise_data)
end = time.time()
print(f"O(N) loop: {end - start:.4f} seconds")

# Assert correctness
for e1, e2 in zip(all_exercises, all_exercises_opt):
    assert e1['label'] == e2['label']
    assert e1['solution'] == e2['solution']
