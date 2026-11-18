"""Add source presentation only, without rewriting any release metadata."""
import copy

def apply_branding(source, config):
    result = copy.deepcopy(source)
    result.update(config['source'])
    owned = {n['identifier'] for n in config.get('news', [])}
    result['news'] = copy.deepcopy(config.get('news', [])) + [n for n in source.get('news', []) if n.get('identifier') not in owned]
    for app in result.get('apps', []):
        app.update(copy.deepcopy(config.get('apps', {}).get(app['bundleIdentifier'], {})))
    return result
