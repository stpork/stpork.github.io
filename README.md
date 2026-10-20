# MDVu website

The product website for [MDVu](https://github.com/stpork/mdvu), hosted at **https://stpork.github.io/mdvu/**.

## Develop

Static HTML and CSS, with small progressive-enhancement scripts. Python 3 builds the pages; Node.js checks browser scripts. No npm dependencies, framework, runtime API calls, analytics, external fonts or third-party scripts.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build.py
python3 scripts/check.py
node --check mdvu/assets/site.js
node --check mdvu/assets/theme.js
node scripts/check-theme.cjs
python3 -m http.server 8765 --bind 127.0.0.1
```

Edit content in `scripts/build.py`, styles in `mdvu/assets/site.css` and interactions in `mdvu/assets/site.js`. Commit all six generated pages and the 404 page after rebuilding. CI checks deterministic output for every generated route before resolving current release assets and rebuilding for deployment.

## Pages and search

The landing page has the app screenshot, Comparison table, overview, Features, installation and FAQ. The menu contains only **Overview, Features, Diagrams**. Features opens with ArchiMate under Architecture, followed by Classes, Flowcharts, Sequence, Math and Callouts tabs, followed by a More… link to the diagram gallery, then the six supported diagram families and Markdown dialects. Diagram examples reuse static SVGs from the verified catalogue; no rendering engine is loaded by the website.

`/mdvu/diagrams/` contains the 73 examples, each with source and the actual MDVu SVG. A visible corner control enlarges every rendered diagram on the landing page or gallery, and the app screenshot. Math and Callouts use the same dialog with a scaled copy of their rendered content. It preserves aspect ratio within both viewport dimensions, closes with Escape/×/backdrop, and restores keyboard focus and scrolling. `/mdvu/performance/` holds detailed cold/warm results and methodology. Russian equivalents live under `/mdvu/ru/`. Performance and Russian pages are available by direct URL and have no entry in the public navigation or English language switcher. All six canonical pages permit indexing and are listed in the sitemap, as requested.

Every page has a distinct title/description, canonical URL, Open Graph/Twitter metadata and SoftwareApplication/WebPage structured data. Search copy uses Markdown viewer, MD viewer and MD file viewer in context. Fast/compact wording describes the product design; no universal fastest-app or memory claim is inferred from a single observation. Keep root redirects and Google verification intact. Submit **https://stpork.github.io/sitemap.xml** in Search Console after publishing.

The site follows system light/dark mode and supports a persistent manual override. Tabs, clipboard copy and a shared screenshot/SVG preview are progressive enhancements; content remains available without JavaScript. `scripts/check-theme.cjs` checks storage and system-change behavior. The share card is 1120×630, generated from `scripts/social.html`; icons and app screenshots originate from the application repo.

## Downloads and release scope

The hero and installation section each provide **macOS · DMG** and **Windows · MSI** buttons. **Other versions · portable ZIPs** links to GitHub Releases. Both installer links come from verified public release assets. The browser's operating system selects the highlighted download and the matching screenshot tab; choosing another screenshot tab switches the highlight too.

Download buttons use permanent GitHub URLs such as `https://github.com/stpork/mdvu/releases/latest/download/mdvu-macos.dmg` and `https://github.com/stpork/mdvu/releases/latest/download/mdvu-windows-x86_64.msi`. Each release contains these stable-name copies alongside the original versioned packages. Historical releases and versioned URLs remain available. New releases need no website source edits, and download links stay current even before a site rebuild.

`mdvu/data/release.json` snapshots the latest public stable release; refresh it with `python3 scripts/update-release.py`. Starting with 0.5.0, metadata refresh rejects releases missing any of the six packages: macOS DMG, ARM/Universal/Intel ZIPs, Windows x64 MSI and ZIP. From 0.5.1 it also verifies stable copies against the original packages' sizes and SHA-256 digests. The deployment build refreshes version metadata automatically. Comparison observations retain their recorded test-build identities; release metadata must not silently relabel benchmark results.

Pull requests to `develop`/`main` and pushes to `develop` run the build and tests without deploying. Only a `main` push or a manual **Deploy MDVu website** dispatch on `main` can deploy; use them only when publication is authorized. GitHub Pages must use GitHub Actions as its source. The application publish helper dispatches this workflow after release. For a manual tag release, refresh the release snapshot and push the regenerated pages to `main`, or dispatch the workflow on `main` when no source change is needed.

## Comparison evidence and synchronization

`mdvu/data/full-pass-performance.json` supplies the eight-app size, cold/warm startup and memory data. `diagram-compatibility.json` supplies the paired 73-case outcomes. The landing table uses rounded installed Universal-app MiB, warm Light memory and warm process-start-to-first-visible Mermaid. Its short **Render · Page** heading has a tooltip explaining that cached SVGs are allowed; **Formats** links to the gallery. Results are macOS-only and individual paired observations. The full study is incomplete (136/192 qualified startup cells, 135/192 verified EOF passes); the detailed page and report retain missing outcomes and historical methods.

`comparison.json` retains earlier versioned competitor/download facts; it is not the source for the landing table's installed sizes or timings. Raw recordings remain outside site assets.

After app documentation or verified results change, synchronize them from the local checkout:

```sh
python3 scripts/sync-app-docs.py /path/to/mdvu
python3 scripts/build.py
python3 scripts/check.py
```

The sync copies the local benchmark protocol and diagram fixture, rewriting relative links in downloadable Markdown so they resolve on the website. Existing versioned results retain their recorded values. Update both language variants together; no local editing step publishes the site.
