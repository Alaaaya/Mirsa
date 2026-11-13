import copy, io, json, plistlib, unittest, zipfile
from latest_normal import latest_normal
class LatestNormalTests(unittest.TestCase):
    def setUp(self):
        self.setup={"name":"Mirsa Setup","bundleIdentifier":"com.alaa.mirsa.setup","version":"2.2","versions":[{"version":"2.2","buildVersion":"4.63.2"}],"iconURL":"same"}
        z=io.BytesIO()
        with zipfile.ZipFile(z,"w") as a:
            a.writestr("Payload/Mirsa.app/Info.plist",plistlib.dumps({"CFBundleIdentifier":"com.alaa.mirsa","CFBundleVersion":"5.58.1","CFBundleShortVersionString":"2.3"}))
        self.ipa=z.getvalue()
        self.notes={k:"note "+k for k in ("ar","en","de","kmr","ckb")}
        self.rel={"tag_name":"2.3","body":json.dumps({"releaseNotes":self.notes}),"published_at":"2026-11-13T22:00:00Z","assets":[{"name":"Mirsa.ipa","size":len(self.ipa),"browser_download_url":"https://github.com/Alaaaya/Mirsa-iOS/releases/download/2.3/Mirsa.ipa"}]}
    def test_normal_advances_setup_untouched(self):
        old=copy.deepcopy(self.setup)
        out=latest_normal(self.setup,self.rel,self.ipa)
        self.assertEqual(self.setup,old)
        self.assertEqual(out["version"],"2.3")
        self.assertEqual(out["versions"][0]["buildVersion"],"5.58.1")
        self.assertEqual(out["versions"][0]["releaseNotes"],self.notes)
    def test_reject_wrong_short_version(self):
        self.rel["tag_name"]="2.4"
        with self.assertRaises(AssertionError): latest_normal(self.setup,self.rel,self.ipa)
    def test_reject_prerelease(self):
        self.rel["prerelease"]=True
        with self.assertRaises(AssertionError): latest_normal(self.setup,self.rel,self.ipa)
    def test_reject_downgrade(self):
        self.setup["version"]="2.4"
        with self.assertRaises(AssertionError): latest_normal(self.setup,self.rel,self.ipa)
if __name__=="__main__": unittest.main()
