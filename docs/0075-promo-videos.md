# Promo videos (short marketing walkthroughs)

How we produce short Satisfecho promo clips: live browser click-around + **copyleft** background music, letterboxed to 1080p.

**Pattern (mac-stats):** The companion project [mac-stats](https://github.com/raro42/mac-stats/) ships `screens/mac-stats-features.mp4` — a live window capture with an ambient bed (see that repo’s `screens/README.md`). For this **web** app we use the same idea with **Puppeteer screencast** instead of ScreenCaptureKit.

## Recorder

| Item | Path / command |
|------|----------------|
| Script | `front/scripts/record-promo-video.mjs` |
| npm | `npm run record-promo-video --prefix front` |
| Outputs (gitignored) | `tmp/promo/*.webm`, `tmp/promo/*.mp4` |
| Default latest alias | `tmp/promo/satisfecho-promo-latest.mp4` |

```bash
# App must be up (local or production)
BASE_URL=http://127.0.0.1:4202 npm run record-promo-video --prefix front
# or
BASE_URL=https://www.satisfecho.de npm run record-promo-video --prefix front
```

**Env:** `BASE_URL`, `OUT_DIR` (default `tmp/promo`), `MUSIC_PATH`, `TENANT_ID` (default `1`), `HEADLESS=0` to watch, `SKIP_ENCODE=1` for raw WebM only. Requires **Google Chrome** (or `PUPPETEER_EXECUTABLE_PATH`) and **ffmpeg** on `PATH`.

### What the script does

1. Launches Chrome via **puppeteer-core** and starts `page.screencast({ path: …webm })` (VP9 / 30fps family; needs ffmpeg).
2. Walks public marketing / guest surfaces with short holds and smooth scrolls:
   `/` → `/features` → `/pricing` → `/book/{tenant}` → `/delivery/{tenant}` → `/about` → `/`
3. Stops the screencast, then **ffmpeg**-muxes:
   - letterbox / pad to **1920×1080**
   - soft music bed (volume + fade in/out)
   - H.264 + AAC MP4 (`+faststart`)

Do **not** full-desktop capture for marketing assets (same privacy rule as mac-stats window-only shots).

## Music (copyleft only)

**Requirement:** beds must be **copyleft** (e.g. **CC BY-SA**), not “mystery free MP3” or unverified example tracks.

| Default bed | Homage — Kjartan Abel |
|-------------|------------------------|
| License | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Source | https://kjartan-abel.com/library/homage/ |
| Local file (gitignored under `tmp/`) | `tmp/promo/Homage-by-Kjartan-Abel.mp3` |

Download (once per machine):

```bash
mkdir -p tmp/promo
curl -L -o tmp/promo/Homage-by-Kjartan-Abel.mp3 \
  https://usercontent.one/wp/kjartan-abel.com/wp-content/uploads/2022/04/Homage-by-Kjartan-Abel.mp3
```

**Attribution** (required when publishing a video that includes this bed):

```text
Homage by Kjartan Abel.
https://kjartan-abel.com/library
Licensed under CC BY-SA 4.0.
```

**ShareAlike:** distributed derivatives that include the bed (including the promo MP4) must be shared under **CC BY-SA 4.0** (or compatible). Do not claim Content ID on the track. Full notes: keep a local `tmp/promo/MUSIC-LICENSE.txt` when producing cuts (template below).

### MUSIC-LICENSE.txt template

```text
Track: Homage
Artist: Kjartan Abel
Source: https://kjartan-abel.com/library/homage/
License: CC BY-SA 4.0 — https://creativecommons.org/licenses/by-sa/4.0/
Attribution: Homage by Kjartan Abel. https://kjartan-abel.com/library — CC BY-SA 4.0.
```

## Publishing checklist

1. Confirm bed license is copyleft (CC BY-SA or similar) and credit is in the description / credits.
2. Prefer production `BASE_URL` for public-facing cuts when demo content looks better there.
3. Keep large binaries out of git (`tmp/` is ignored); store published assets where marketing hosts them.
4. If you change the walkthrough routes, update this doc and the script’s `runWalkthrough` in lockstep.

## Related

- Still screenshots: [screenshots/README.md](screenshots/README.md), `front/scripts/capture-screenshots.mjs`
- Puppeteer suite overview: [testing.md](testing.md)
- Public routes: root [README.md](../README.md) (features, about, book, delivery)
