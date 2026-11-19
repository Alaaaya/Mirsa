"""Exercise the real generator statements against legacy installed updater logic."""
import ast
import copy
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / 'scripts/sync.py').read_text())
# The assignment removes any previous normal entry; the following insert orders it.
START = next(i for i, node in enumerate(TREE.body)
             if isinstance(node, ast.Assign) and isinstance(node.value, ast.ListComp))
ORDER = compile(ast.fix_missing_locations(ast.Module(
    body=TREE.body[START:START + 2], type_ignores=[])), '<real-sync-order>', 'exec')

def reorder(source, normal):
    scope = dict(source=source, normal=normal)
    exec(ORDER, scope)
    return scope['source']

def first_prefix(feed):
    return next(a for a in feed['apps']
                if a['bundleIdentifier'].startswith('com.alaa.mirsa'))

class SyncOrderTests(unittest.TestCase):
    def setUp(self):
        self.feed = json.loads((ROOT / 'source.json').read_text())
        self.normal = next(a for a in self.feed['apps']
                           if a['bundleIdentifier'] == 'com.alaa.mirsa')

    def test_legacy_client_sees_new_normal_not_setup(self):
        old = copy.deepcopy(self.feed)
        old['apps'].sort(key=lambda a: a['bundleIdentifier'] != 'com.alaa.mirsa.setup')
        self.assertEqual(first_prefix(old)['bundleIdentifier'], 'com.alaa.mirsa.setup')
        new = reorder(old, copy.deepcopy(self.normal))
        self.assertEqual(first_prefix(new), self.normal)
        build = tuple(map(int, first_prefix(new)['versions'][0]['buildVersion'].split('.')))
        self.assertGreater(build, (6, 90, 1))

    def test_all_fields_and_independent_relative_order_unchanged(self):
        old = copy.deepcopy(self.feed)
        before = copy.deepcopy(old)
        new = reorder(old, copy.deepcopy(self.normal))
        self.assertEqual({a['bundleIdentifier']: a for a in before['apps']},
                         {a['bundleIdentifier']: a for a in new['apps']})
        self.assertEqual([a for a in before['apps'] if a['bundleIdentifier'] != 'com.alaa.mirsa'],
                         new['apps'][1:])
        self.assertEqual({k:v for k,v in before.items() if k != 'apps'},
                         {k:v for k,v in new.items() if k != 'apps'})

    def test_missing_normal_inserted_first_and_repeated_sync_idempotent(self):
        feed = copy.deepcopy(self.feed)
        feed['apps'] = [a for a in feed['apps'] if a['bundleIdentifier'] != 'com.alaa.mirsa']
        once = reorder(feed, copy.deepcopy(self.normal))
        twice = reorder(copy.deepcopy(once), copy.deepcopy(self.normal))
        self.assertEqual(once, twice)
        self.assertEqual(first_prefix(twice), self.normal)
        self.assertEqual(sum(a['bundleIdentifier'] == 'com.alaa.mirsa' for a in twice['apps']), 1)

if __name__ == '__main__':
    unittest.main()
