import warnings

def log(obj, msg):
    print(f"[{obj}] {msg}")
    
def warn(obj, msg):
    warnings.warn(f"[{obj}] {msg}")
