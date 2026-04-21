import time
from pathlib import Path

# Create nested mock dict
materials = []
for i in range(1000):
    materials.append({
        'frontmatter': {
            'subject': f"Subject {i % 10}",
            'tags': [f"tag{j}" for j in range(5)],
            'keywords': [f"kw{j}" for j in range(5)]
        }
    })

def test_original(topic):
    start = time.time()
    for _ in range(100):
        found = []
        for material in materials:
            subject_match = material['frontmatter'].get('subject', '').lower().find(topic.lower()) != -1
            tags_match = any(topic.lower() in tag.lower() for tag in material['frontmatter'].get('tags', []))
            keywords_match = any(topic.lower() in kw.lower() for kw in material['frontmatter'].get('keywords', []))
            if subject_match or tags_match or keywords_match:
                found.append(material)
    return time.time() - start

def test_optimized(topic):
    start = time.time()
    for _ in range(100):
        found = []
        topic_lower = topic.lower()
        for material in materials:
            frontmatter = material['frontmatter']

            subject = frontmatter.get('subject', '')
            if subject and topic_lower in subject.lower():
                found.append(material)
                continue

            tags = frontmatter.get('tags', [])
            if any(topic_lower in tag.lower() for tag in tags):
                found.append(material)
                continue

            keywords = frontmatter.get('keywords', [])
            if any(topic_lower in kw.lower() for kw in keywords):
                found.append(material)
    return time.time() - start

print(f"Original: {test_original('subject 5'):.4f}s")
print(f"Optimized: {test_optimized('subject 5'):.4f}s")
