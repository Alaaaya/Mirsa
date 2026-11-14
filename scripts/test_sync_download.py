import ast
import io
import os
import pathlib
import unittest
import urllib.request
import urllib.parse
from unittest.mock import patch

tree = ast.parse(pathlib.Path(__file__).with_name('sync.py').read_text())
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'download')
scope = dict(urllib=__import__('urllib'), os=os)
exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), '<download>', 'exec'), scope)
download = scope['download']

class DownloadTests(unittest.TestCase):
    def test_api_authenticated_without_redirect(self):
        with patch.dict(os.environ, GH_TOKEN='private-test'), patch('urllib.request.build_opener') as build:
            build.return_value.open.return_value = io.BytesIO(b'ok')
            self.assertEqual(download('https://api.github.com/repos/a/b/releases/latest'), b'ok')
            req = build.return_value.open.call_args.args[0]
            self.assertEqual(req.get_header('Authorization'), 'Bearer private-test')
            with self.assertRaises(ValueError):
                build.call_args.args[0].redirect_request(None,None,None,None,None,None)
    def test_asset_and_lookalike_never_receive_token(self):
        for host in ['github.com', 'release-assets.githubusercontent.com', 'api.github.com.evil.example']:
            with patch.dict(os.environ, GH_TOKEN='private-test'), patch('urllib.request.urlopen') as fetch:
                fetch.return_value = io.BytesIO(b'ok')
                self.assertEqual(download('https://'+host+'/asset'), b'ok')
                self.assertIsNone(fetch.call_args.args[0].get_header('Authorization'))
    def test_http_rejected(self):
        with self.assertRaises(ValueError):
            download('http://github.com/asset')
if __name__ == '__main__':
    unittest.main()
