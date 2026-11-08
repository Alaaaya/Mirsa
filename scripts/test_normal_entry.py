import copy
import io
import plistlib
import unittest
import zipfile
from normal_entry import normal_entry

class NormalEntryTests(unittest.TestCase):
    def setUp(self):
        self.setup = {"name": "Mirsa Setup", "bundleIdentifier": "com.alaa.mirsa.setup",
            "version": "1.3.205", "iconURL": "same-icon", "versions": [{
                "version": "1.3.205", "releaseNotes": {"ar": "إصلاح", "en": "Fix"}}]}
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("Payload/Mirsa.app/Info.plist", plistlib.dumps({
                "CFBundleIdentifier": "com.alaa.mirsa", "CFBundleVersion": "4.5.1",
                "MirsaBuild": "205"}))
        self.ipa = out.getvalue()
        self.release = {"tag_name": "1.3.205", "assets": [{"name": "Mirsa.ipa",
            "size": len(self.ipa), "browser_download_url":
                "https://github.com/Alaaaya/Mirsa-iOS/releases/download/1.3.205/Mirsa.ipa"}]}

    def test_entry_and_preservation(self):
        before = copy.deepcopy(self.setup)
        result = normal_entry(self.setup, self.release, self.ipa)
        self.assertEqual(self.setup, before)
        self.assertEqual(result["bundleIdentifier"], "com.alaa.mirsa")
        self.assertEqual(result["iconURL"], self.setup["iconURL"])
        self.assertEqual(result["versions"][0]["releaseNotes"], self.setup["versions"][0]["releaseNotes"])

    def test_mismatch_rejected(self):
        self.release["tag_name"] = "1.3.204"
        with self.assertRaises(AssertionError):
            normal_entry(self.setup, self.release, self.ipa)

    def test_truncation_rejected(self):
        with self.assertRaises(AssertionError):
            normal_entry(self.setup, self.release, self.ipa[:-1])

    def test_wrong_url_rejected(self):
        self.release["assets"][0]["browser_download_url"] = "https://example.com/other.ipa"
        with self.assertRaises(AssertionError):
            normal_entry(self.setup, self.release, self.ipa)

if __name__ == "__main__":
    unittest.main()
