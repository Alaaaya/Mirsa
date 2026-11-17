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
    def test_independent_source_metadata_is_not_inherited(self):
        self.setup.update(sourceURL="old-source", sourceSHA256="old-digest", license="old")
        self.setup["versions"][0].update(sourceURL="old-source", sourceSHA256="old-digest")
        out=latest_normal(self.setup,self.rel,self.ipa)
        self.assertNotIn("sourceURL",out)
        self.assertNotIn("sourceURL",out["versions"][0])
    def test_matching_source_metadata_propagates_without_changing_setup(self):
        metadata={"releaseNotes":self.notes,"license":"GPL-3.0",
                  "sourceURL":"https://github.com/Alaaaya/Mirsa-iOS/releases/download/2.3/Mirsa-2.3-source.tar.gz",
                  "sourceSHA256":"a"*64}
        self.rel["body"]=json.dumps(metadata)
        old=copy.deepcopy(self.setup)
        out=latest_normal(self.setup,self.rel,self.ipa)
        self.assertEqual(self.setup,old)
        for obj in (out,out["versions"][0]):
            self.assertEqual(obj["sourceURL"],metadata["sourceURL"])
            self.assertEqual(obj["sourceSHA256"],metadata["sourceSHA256"])
    def test_reject_source_for_another_release(self):
        self.rel["body"]=json.dumps({"releaseNotes":self.notes,"license":"GPL-3.0",
                  "sourceURL":"https://github.com/Alaaaya/Mirsa-iOS/releases/download/2.2/old.tar.gz","sourceSHA256":"a"*64})
        with self.assertRaises(AssertionError):latest_normal(self.setup,self.rel,self.ipa)
    def test_reject_bad_source_digest(self):
        self.rel["body"]=json.dumps({"releaseNotes":self.notes,"license":"GPL-3.0",
                  "sourceURL":"https://github.com/Alaaaya/Mirsa-iOS/releases/download/2.3/source.tar.gz","sourceSHA256":"invalid"})
        with self.assertRaises(AssertionError):latest_normal(self.setup,self.rel,self.ipa)
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
