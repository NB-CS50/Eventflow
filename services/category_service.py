"""Prepare event category choices."""

def flatten_categories(category_tree, prefix=""):
    """Turn nested categories into one list."""
    result = []
    for name, children in category_tree.items():
        label = f"{prefix} > {name}" if prefix else name
        result.append(label)
        if isinstance(children, dict) and children:
            result.extend(flatten_categories(children, label))
    return result
