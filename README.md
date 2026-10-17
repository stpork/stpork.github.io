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

The hero links to GitHub Releases. DMG and MSI are the installation buttons. **Others** links to GitHub Releases for portable macOS ARM, Universal, Intel and Windows x64 ZIPs. No download URL is invented: MSI links to the releases index until an installer is published. Starting with 0.5.0, metadata refresh rejects incomplete six-package releases. After an app release, its publish helper dispatches this website workflow; manual tag releases need the same dispatch.

Pages remain usable without JavaScript. No runtime API calls, analytics, external fonts or third-party scripts. Clipboard copy, accessible tabs, screenshot preview and theme selection are progressive enhancements.

## Performance comparison

`mdvu/data/comparison.json` holds versioned competitor facts, compressed package byte counts and source links. The page compares MDVu, Typora, Obsidian, Marked and VS Code. Package formats and architectures are explicit. Unknown values remain absent; startup/rendering numbers require a common test protocol. The internal native UI report does not belong on the product landing page.

Update both language variants together. Keep product copy factual and concise. The hero links to GitHub Releases; platform installers and portable alternatives appear in the installation section.

## Presentation and search

The site follows the system light/dark preference and offers a persistent manual override. `theme.js` runs before the stylesheet to avoid a theme flash; `scripts/check-theme.cjs` checks storage and system-change behavior.

The English page is the public entry point. The Russian page is accessible by direct URL, has noindex, and is absent from public language links and the sitemap. Keep root redirects and Google verification intact. Submit **https://stpork.github.io/sitemap.xml** in Search Console. The static checker validates links, metadata, release availability, comparison data and asset budgets.

`mdvu/assets/social.jpg` is the 1200×630 share card rendered from `scripts/social.html`. The icon and real app screenshot originate from the MDVu repository. Responsive WebP images have a JPEG fallback.
