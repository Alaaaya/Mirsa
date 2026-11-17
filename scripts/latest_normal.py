"""Keep normal app releases independent from the bootstrap Setup channel."""
import copy
import io
import json
import plistlib
import re
import zipfile
from normal_entry import normal_entry

def latest_normal(setup, release, ipa):
    assert not release.get("draft") and not release.get("prerelease")
    version = release["tag_name"]
    assert len(version.split(".")) == 2 and all(n.isdigit() for n in version.split("."))
    assert tuple(map(int, version.split("."))) >= tuple(map(int, setup["version"].split(".")))
    metadata = json.loads(release["body"])
    notes = metadata["releaseNotes"]
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
    entry = normal_entry(template, release, ipa)
    # The bootstrap app can stay on an older version. Its corresponding source
    # must never be advertised as source for a newer independent normal release.
    for container in (entry, entry["versions"][0]):
        for key in ("sourceURL", "sourceSHA256", "license"):
            container.pop(key, None)
    if any(key in metadata for key in ("sourceURL", "sourceSHA256", "license")):
        source_url = metadata["sourceURL"]
        source_sha = metadata["sourceSHA256"]
        assert source_url.startswith(
            "https://github.com/Alaaaya/Mirsa-iOS/releases/download/" + version + "/"
        ), "Corresponding source must belong to this normal release"
        assert re.fullmatch(r"[0-9a-f]{64}", source_sha), "Invalid source digest"
        assert metadata["license"] == "GPL-3.0"
        for container in (entry, entry["versions"][0]):
            container.update(sourceURL=source_url, sourceSHA256=source_sha)
        entry["license"] = metadata["license"]
    return entry
