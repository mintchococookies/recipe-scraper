import re

def postprocess_list(lst):
    if lst:
        return [re.sub(r'^\s*▢\s*', '', item) for item in lst]
    else:
        return None

def postprocess_text(txt):
    return txt.strip()