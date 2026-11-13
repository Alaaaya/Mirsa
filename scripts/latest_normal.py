"""Keep normal app releases independent from the bootstrap Setup channel."""
import copy
import io
import json
import plistlib
import zipfile
from normal_entry import normal_entry

def latest_normal(setup, release, ipa):
    assert not release.get("draft") and not release.get("prerelease")
    version = release["tag_name"]
    assert len(version.split(".")) == 2 and all(n.isdigit() for n in version.split("."))
    assert tuple(map(int, version.split("."))) >= tuple(map(int, setup["version"].split(".")))
    notes = json.loads(release["body"])["releaseNotes"]
    assert all(isinstance(v, str) and v.strip() for v in notes.values())
    assert {"ar", "en", "kmr", "ckb"}.issubset(notes)
    with zipfile.ZipFile(io.BytesIO(ipa)) as archive:
        assert archive.testzip() is None
        path = next(n for n in archive.namelist() if n.startswith("Payload/") and n.count("/") == 2 and n.endswith("/Info.plist"))
        info = plistlib.loads(archive.read(path))
    template = copy.deepcopy(setup)
    template.update(version=version, versionDate=release["published_at"])
    current = template["versions"][0]
    current.update(version=version, buildVersion=str(info["CFBundleVersion"]), date=release["published_at"], releaseNotes=notes)
    return normal_entry(template, release, ipa)
