# MDVu website

The official product website for [MDVu](https://github.com/stpork/mdvu), published at **https://stpork.github.io/**.

English: `/`. Russian: `/ru/`. `/mdvu/` redirects to the homepage.

## Develop

No npm dependencies or framework. Requires Python 3 for generation and Node.js only for the JavaScript syntax check.

```sh
python3 scripts/build.py
python3 scripts/check.py
node --check assets/site.js
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/. Edit copy in `scripts/build.py`, styling in `assets/site.css`, interactions in `assets/site.js`. Commit both generated HTML files after changing the generator. GitHub Actions verifies the generated files and deploys only public assets.

## Publishing

Push to `main`. The `Deploy MDVu website` workflow validates and deploys to GitHub Pages (Pages source must be **GitHub Actions**).

The public site needs no JavaScript to read the content, follow download links or use the FAQ. The small script adds clipboard copy, accessible tabs and the screenshot dialog. No third-party scripts, external fonts, analytics or runtime API calls.

## Release update checklist

1. Update `RELEASE`, `DOWNLOAD`, release numbers and archive links in `scripts/build.py`.
2. Verify sizes against GitHub release assets; distinguish native app allocation from Universal app size and compressed download size.
3. Update benchmark values only from a recorded run; retain measurement scope and methodology.
4. Recheck comparison sources and update the checked date.
5. Update `sitemap.xml` modification dates. Generate and validate both pages.
6. Keep the Google site-verification meta tag in the homepage head. The English page intentionally has no RU switch; the Russian page retains its EN switch. Both remain discoverable through hreflang and sitemap.

`assets/social.jpg` is the 1200×630 rendered share card; `scripts/social.html` is its source. The icon and application screenshot originate from the MDVu repository. The app screenshot is delivered as responsive WebP with a JPEG fallback.

Product facts: MDVu README, architecture and v0.4.1 changelog/release. Comparison sources are linked immediately below the comparison table. Site copy does not claim competitor benchmark results, notarization or unsupported editor functionality.
