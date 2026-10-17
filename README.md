# MDVu website

The official product website for [MDVu](https://github.com/stpork/mdvu), published at **https://stpork.github.io/mdvu/**.

## Develop

Static HTML, CSS and a small script; no npm dependencies or framework. Python 3 generates the pages; Node.js checks the client scripts.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build.py
python3 scripts/check.py
node --check mdvu/assets/site.js
node --check mdvu/assets/theme.js
node scripts/check-theme.cjs
python3 -m http.server 8765 --bind 127.0.0.1
```

Edit copy in `scripts/build.py`, styles in `mdvu/assets/site.css` and interactions in `mdvu/assets/site.js`. Commit the generated pages after changing the generator. The workflow checks deterministic output before resolving current release assets and rebuilding for deployment.

## Downloads and publishing

Push to `main` or dispatch **Deploy MDVu website**. GitHub Pages must use GitHub Actions as its source. The workflow runs `scripts/update-release.py` to query the latest stable GitHub Release at build time. `mdvu/data/release.json` is the checked-in snapshot for local builds; refresh it with the same command.

DMG and MSI are the primary buttons. **Others** links to GitHub Releases for portable macOS ARM, Universal, Intel and Windows x64 ZIPs. No download URL is invented: older macOS-only releases show MSI as upcoming. Starting with 0.5.0, metadata refresh rejects incomplete six-package releases. After an app release, its publish helper dispatches this website workflow; manual tag releases need the same dispatch.

Pages remain usable without JavaScript. No runtime API calls, analytics, external fonts or third-party scripts. Clipboard copy, accessible tabs, screenshot preview and theme selection are progressive enhancements.

## Measurements and copy

`mdvu/data/measurements.json` records build 0.5.0 / commit `40892c5`, package hashes and sizes from CI run 39052275911, and real native before/after measurements from 37 fixtures per OS. It contains all fixture metrics and all five scroll-pass frame arrays, with frame intervals rounded to 0.001 ms. It excludes local paths, account names and transport details.

The page derives its tables from that file. Keep measured revision/date separate from the current download version. Distinguish compressed download, installed app, executable, system runtime and process memory. Frame intervals are not input latency; document-ready is not completion of every diagram. Preserve regressions and test conditions. This is not a competitor benchmark or a claim of complete compatibility with every Markdown ecosystem plugin.

When refreshing evidence, replace the recorded dataset, check the visible tables and methodology, then update `sitemap.xml` dates. Product capabilities come from the app README and source. Snapshot PNG export is macOS-only; HTML export works on both platforms.

## Presentation and search

The site follows the system light/dark preference and offers a persistent manual override. `theme.js` runs before the stylesheet to avoid a theme flash; `scripts/check-theme.cjs` checks storage and system-change behavior.

Keep canonical URLs, reciprocal language annotations, root redirects, Google verification and sitemap entries consistent. Submit **https://stpork.github.io/sitemap.xml** in Search Console. The static checker validates links, metadata, release availability, measurement aggregates and asset budgets.

`mdvu/assets/social.jpg` is the 1200×630 share card rendered from `scripts/social.html`. The icon and real app screenshot originate from the MDVu repository. Responsive WebP images have a JPEG fallback.
