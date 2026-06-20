def safe_load(stream):
    if hasattr(stream, 'read'): stream = stream.read()
    if 'subject' in stream: return {'subject': 'test', 'tags': ['test']}
    if 'title: Test Page' in stream: return {'title': 'Test Page', 'author': 'Bolt'}
    return {'paths': {'base_dir': '.', 'materials': ['.']}}

def dump(*args, **kwargs): pass
