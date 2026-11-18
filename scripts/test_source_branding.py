import copy,json,pathlib,unittest
from source_branding import apply_branding
class BrandingTests(unittest.TestCase):
 def test_real_config_preserves_versions_notes_and_other_apps(self):
  root=pathlib.Path(__file__).resolve().parents[1];old=json.loads((root/'source.json').read_text());cfg=json.loads((root/'branding.json').read_text());new=apply_branding(old,cfg)
  self.assertEqual(new,apply_branding(new,cfg))
  for a,b in zip(old['apps'],new['apps']):
   for key,value in a.items():
    if key not in cfg['apps'].get(a['bundleIdentifier'],{}):self.assertEqual(value,b[key])
  self.assertEqual(new['website'],'https://x.com/rasmtk30')
  self.assertEqual(new['news'][0]['url'],new['website'])
  self.assertNotIn('2.7',json.dumps(cfg))
 def test_existing_news_and_independent_apps_survive(self):
  old={'name':'old','news':[{'identifier':'older','title':'retain'}],'apps':[{'bundleIdentifier':'other','versions':[{'version':'9','releaseNotes':{'ar':'نص'}}]}]};before=copy.deepcopy(old)
  new=apply_branding(old,{'source':{'tintColor':'7C83FF'},'news':[{'identifier':'welcome'}]})
  self.assertEqual(old,before);self.assertEqual(old['apps'],new['apps']);self.assertEqual(new['news'][1],old['news'][0])
