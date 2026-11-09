"""Derive the standard signed-by-installer app from the matching setup version."""
import copy
import io
import plistlib
import zipfile

def normal_entry(setup, release, ipa):
    version = setup["version"]
    assert release["tag_name"] == version, "Normal release must match setup"
    assert not release.get("prerelease") and not release.get("draft")
    assets = [a for a in release["assets"] if a["name"] == "Mirsa.ipa"]
    assert len(assets) == 1, "Missing unique normal IPA"
    asset = assets[0]
    expected = f"https://github.com/Alaaaya/Mirsa-iOS/releases/download/{version}/Mirsa.ipa"
    assert asset["browser_download_url"] == expected
    assert len(ipa) == asset["size"], "Normal IPA size mismatch"
    with zipfile.ZipFile(io.BytesIO(ipa)) as archive:
        assert archive.testzip() is None, "Corrupt normal IPA"
        info = plistlib.loads(archive.read(next(n for n in archive.namelist()
            if n.startswith("Payload/") and n.count("/") == 2 and n.endswith("/Info.plist"))))
    assert info["CFBundleIdentifier"] == "com.alaa.mirsa", "Wrong normal bundle"
    # Short marketing versions are independent of the CI run number.
    expected_build = setup["versions"][0].get("buildVersion")
    if expected_build:
        assert str(info["CFBundleVersion"]) == str(expected_build), "Wrong normal build"
    else:
        # Historical feeds did not always publish buildVersion.
        assert str(info["MirsaBuild"]) == version.rsplit(".", 1)[1], "Wrong normal build"
    if len(version.split(".")) == 2:
        assert expected_build, "Short versions require an explicit setup build"
        assert info.get("CFBundleShortVersionString") == version, "Wrong normal short version"
    entry = copy.deepcopy(setup)
    entry.update(name="Mirsa", bundleIdentifier="com.alaa.mirsa",
                 localizedDescription="Mirsa. Requires signing by your installer.",
                 downloadURL=expected, size=len(ipa))
    entry["versions"] = [copy.deepcopy(setup["versions"][0])]
    entry["versions"][0].update(downloadURL=expected, size=len(ipa),
        buildVersion=str(info["CFBundleVersion"]), localizedDescription="Mirsa " + version)
    return entry
