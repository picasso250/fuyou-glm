"""
Core Skill: Persistence
Provides file persistence utilities for digital life
"""

import os

def ensure_persistence(path, content):
    """Guarantee content is written to path"""
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except:
        return False

def load_with_fallback(paths):
    """Try loading from multiple paths, return first success"""
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            continue
    return None
