# Mirsa

Add this source to your installer:

https://github.com/Alaaaya/Mirsa/releases/download/setup/source.json

The source, icon and setup package use Mirsa URLs. A scheduled workflow checks for new successfully published setup builds every 15 minutes. GitHub may delay scheduled runs. It can also be run manually. No personal access token is stored in this repository.

Packages are mirrored unchanged, preserving their bundle identifier and version. This repository does not rebuild the application.

Alaa Player 2.9 is also included as the unchanged user-provided IPA. Its entry is kept in extra-apps.json and appended on every synchronization, so upstream setup updates do not remove it. The package requires signing by a compatible installer. Its icon is extracted from the package.

## Legal and source

Mirsa is based on [AirCard-iOS](https://github.com/Alaaaya/AirCard-iOS) and the upstream [mak5er project](https://github.com/mak5er/AirCard-iOS). Upstream contributors include mak5er, merybist and Johnny Franks (0xjohnnydev, AirLift). NeoSpring credits include skadz108, rooootdev and neonmodder123. The complete application source and further credits are available in those repositories.

Original copyright and license notices are preserved in LICENSE and LICENSES. Source branding is not a claim of sole authorship.
