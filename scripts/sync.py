"""Mirror the public setup release without modifying its binary or upstream repo."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

UPSTREAM = "https://github.com/Alaaaya/AirCard-iOS/releases/download/setup/"
PUBLIC = "https://github.com/Alaaaya/Mirsa/releases/download/setup/"
OUT = Path("mirror")
OUT.mkdir(exist_ok=True)

def download(url):
    if not url.startswith("https://"):
        raise ValueError("HTTPS required")
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()

source = json.loads(download(UPSTREAM + "source.json"))
app = source["apps"][0]
ipa = download(app["downloadURL"])
assert len(ipa) == app["size"], "Upstream release changed while downloading; retry next run"
import io, zipfile, plistlib
with zipfile.ZipFile(io.BytesIO(ipa)) as archive:
    assert archive.testzip() is None
    info = plistlib.loads(archive.read(next(n for n in archive.namelist() if n.startswith("Payload/") and n.count("/") == 2 and n.endswith("/Info.plist"))))
assert info["CFBundleIdentifier"] == app["bundleIdentifier"]
assert info["CFBundleShortVersionString"] == app["version"]
icon = download(app["iconURL"])
app["iconURL"] = PUBLIC + "Mirsa.png"
app["downloadURL"] = PUBLIC + "Mirsa-Setup.ipa"
for version in app.get("versions", []):
    version["downloadURL"] = PUBLIC + "Mirsa-Setup.ipa"
    version["localizedDescription"] = "Mirsa Setup " + version["version"]
source["name"] = "Mirsa"
source["iconURL"] = PUBLIC + "Mirsa.png"  # source icon (Feather, SideStore, Mirsa)
# Repository-owned entries survive every upstream refresh.
extra_apps = json.loads(Path("extra-apps.json").read_text())
seen = {entry["bundleIdentifier"] for entry in source["apps"]}
for extra in extra_apps:
    assert extra["bundleIdentifier"] not in seen, "Duplicate app bundle identifier"
    assert extra["downloadURL"].startswith(PUBLIC), "Extra apps must use Mirsa assets"
    source["apps"].append(extra)
    seen.add(extra["bundleIdentifier"])
encoded = (json.dumps(source, indent=2) + "\n").encode()
assert b"aircard" not in encoded.lower()
(OUT / "source.json").write_bytes(encoded)
(OUT / "Mirsa-Setup.ipa").write_bytes(ipa)
(OUT / "Mirsa.png").write_bytes(icon)
fingerprint = hashlib.sha256(encoded + ipa + icon).hexdigest()
try:
    previous = download(PUBLIC + "sync.sha256").decode().strip()
except Exception:
    previous = ""
if previous == fingerprint and not os.environ.get("FORCE_SYNC"):
    print("Already synchronized", app["version"])
else:
    (OUT / "sync.sha256").write_text(fingerprint + "\n")
    repo = "Alaaaya/Mirsa"
    found = subprocess.run(["gh", "release", "view", "setup", "--repo", repo], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not found:
        subprocess.run(["gh", "release", "create", "setup", "--repo", repo, "--title", "Mirsa Setup", "--notes", "Mirsa installation source. Legal notices and source attribution are in the repository.", "--latest=false"], check=True)
    # Publish metadata last so clients never see a new version before its binary.
    for filename in ["Mirsa-Setup.ipa", "Mirsa.png", "sync.sha256", "source.json"]:
        subprocess.run(["gh", "release", "upload", "setup", str(OUT / filename), "--repo", repo, "--clobber"], check=True)
    print("Published", app["version"], "bytes", len(ipa), "SHA256", hashlib.sha256(ipa).hexdigest())
