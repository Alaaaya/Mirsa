"""Mirror the public setup release without modifying its binary or upstream repo."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import urllib.parse
from latest_normal import latest_normal

UPSTREAM = "https://github.com/Alaaaya/Mirsa-iOS/releases/download/setup/"
PUBLIC = "https://github.com/Alaaaya/Mirsa/releases/download/setup/"
OUT = Path("mirror")
OUT.mkdir(exist_ok=True)

def download(url):
    if not url.startswith("https://"):
        raise ValueError("HTTPS required")
    # Use the workflow's repository token only on the GitHub API. Shared runner
    # anonymous API limits are often exhausted. Never forward it to asset hosts.
    headers = {"User-Agent": "Mirsa-source-sync"}
    authenticated = urllib.parse.urlsplit(url).hostname == "api.github.com" and os.environ.get("GH_TOKEN")
    if authenticated:
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                raise ValueError("Authenticated API redirects are not allowed")
        opener = urllib.request.build_opener(NoRedirect())
        response = opener.open(urllib.request.Request(url, headers=headers), timeout=120)
    else:
        response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)
    with response:
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
# Normal releases can advance without rebuilding the independent Setup app.
release_url = "https://api.github.com/repos/Alaaaya/Mirsa-iOS/releases/latest"
release = json.loads(download(release_url))
normal_asset = next(a for a in release["assets"] if a["name"] == "Mirsa.ipa")
normal_ipa = download(normal_asset["browser_download_url"])
normal = latest_normal(app, release, normal_ipa)
source["apps"] = [a for a in source["apps"] if a["bundleIdentifier"] != "com.alaa.mirsa"]
source["apps"].insert(1, normal)
# Repository-owned entries survive every upstream refresh.
extra_apps = json.loads(Path("extra-apps.json").read_text())
seen = {entry["bundleIdentifier"] for entry in source["apps"]}
for extra in extra_apps:
    assert extra["bundleIdentifier"] not in seen, "Duplicate app bundle identifier"
    assert extra["downloadURL"].startswith(PUBLIC), "Extra apps must use Mirsa assets"
    source["apps"].append(extra)
    seen.add(extra["bundleIdentifier"])
# Apply repository-owned screenshot metadata after deriving independent entries.
screenshot_map = json.loads(Path("screenshots.json").read_text())
for entry in source["apps"]:
    urls = screenshot_map.get(entry["bundleIdentifier"])
    if urls is not None:
        assert all(url.startswith("https://") for url in urls)
        entry["screenshotURLs"] = urls
        entry["screenshots"] = {"iphone": urls}
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

# Direct static endpoint is committed by the workflow only after release publication
# succeeds (or the matching release is already synchronized).
Path("source.json").write_bytes(encoded)
