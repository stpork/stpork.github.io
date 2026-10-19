#!/usr/bin/env python3
"""Static release checks for links, localization, metadata and page budgets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re
from datetime import date
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set(); self.links = []; self.images = []; self.meta = {}; self.tags=[]
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.tags.append((tag,a))
        if 'id' in a:
            assert a['id'] not in self.ids, f'Duplicate id: {a["id"]}'
            self.ids.add(a['id'])
        if tag == 'meta': self.meta[a.get('name',a.get('property',''))] = a.get('content')
        if tag in ['a','link'] and 'href' in a: self.links.append(a['href'])
        if tag in ['img','script'] and 'src' in a: self.links.append(a['src'])
        if tag == 'img':
            assert 'alt' in a and 'width' in a and 'height' in a
        if 'srcset' in a: self.links += [item.strip().split()[0] for item in a['srcset'].split(',')]

seo_titles = set()
seo_descriptions = set()
linked_page_ids = {}
verification_path = ROOT/'mdvu/data/verification-2026-10-19.json'
if verification_path.exists():
    verification = json.loads(verification_path.read_text())
    assert verification['complete'] and verification['date'] == '2026-10-19'
    names = {app['name'] for app in verification['apps']}
    assert len(names) == 8
    rows = verification['measurements']
    keys = {(r['app'], r['fixture'], r['cacheState']) for r in rows}
    assert len(keys) == len(rows) == 38
    assert all((name, fixture, phase) in keys for name in names for fixture in ['common-test-light.md', 'diagram-control.md'] for phase in ['cold', 'warm'])
    for row in rows:
        assert row['verifiedEOF'] and 'all XPC/system services' in row['samplerAttribution']
        assert re.fullmatch('[0-9a-f]{64}', row['sourceSha256'])
        assert row['memory']['peakMiBFullPass'] >= row['memory']['medianMiBAt8s'] > 0
        if row['fixture'] in ['test-complete.md', 'test-heavy.md']:
            assert row['memory']['medianMiBAfterEOF'] > 0
        if row['app'] == 'MD Viewer' and row['fixture'] == 'diagram-control.md':
            assert 'launchToContentMs' not in row['timing']
        elif row['fixture'] in ['common-test-light.md', 'diagram-control.md']:
            assert row['timing']['launchToContentMs'] > 0
    for fixture in {r['fixture'] for r in rows}:
        assert len({r['sourceSha256'] for r in rows if r['fixture'] == fixture}) == 1
    assert {row['app'] for row in verification['empty']} == {'MDVu', 'MacDown 3000'}
    print('PASS current comparison: complete pairs, consistent inputs, process ownership and explicit timing scope')
for lang in ('en','ru'):
 for section in ('','performance/','diagrams/'):
    rel = 'mdvu/' + ('ru/' if lang=='ru' else '') + section + 'index.html'
    source = (ROOT/rel).read_text(); page = Page(source)
    title = re.search(r'<title>(.*?)</title>', source).group(1)
    assert title not in seo_titles and page.meta['description'] not in seo_descriptions, 'Duplicate page search text'
    seo_titles.add(title); seo_descriptions.add(page.meta['description'])
    assert 15 <= len(title) <= 90 and 'MDVu' in title
    assert page.meta['og:title'] == page.meta['twitter:title'] == title.replace('&amp;', '&')
    assert page.meta['og:description'] == page.meta['twitter:description'] == page.meta['description']
    assert source.startswith('<!doctype html>')
    assert f'<html lang="{lang}">' in source
    assert sum(tag=='h1' for tag,_ in page.tags)==1
    assert page.meta['google-site-verification']=='8hoHZ7azFNVSv9x07AUhAS5xpXH3vrk-LlH07z-cgBc'
    assert source.index('google-site-verification') < source.index('</head>') < source.index('<body>')
    assert 90 <= len(page.meta['description']) <= 180
    assert page.meta['twitter:card']=='summary_large_image'
    assert page.meta['color-scheme']=='light dark'
    assert source.index('/mdvu/assets/theme.js') < source.index('/mdvu/assets/site.css')
    assert sum(tag=='button' and 'data-theme-toggle' in attrs for tag,attrs in page.tags)==1
    assert 'class="language"' not in source if lang=='en' else 'hreflang="en">EN</a>' in source
    assert not any(tag=='link' and a.get('rel')=='alternate' for tag,a in page.tags)
    assert 'noindex' not in page.meta['robots'] and 'index' in page.meta['robots']
    if lang == 'en':
        assert '/mdvu/ru/' not in source
    structured = source.split('<script type="application/ld+json">')[1].split('</script>')[0]
    data=json.loads(structured)
    assert data['@graph'][0]['offers']['price']=='0'
    assert data['@graph'][2]['@type']=='WebPage'
    assert data['@graph'][2]['inLanguage']==lang
    canonical_url = 'https://stpork.github.io/mdvu/' + ('ru/' if lang=='ru' else '') + section
    assert page.meta['og:url']==canonical_url
    assert data['@graph'][0]['url']=='https://stpork.github.io/mdvu/'
    assert data['@graph'][2]['url']==canonical_url
    screenshots = data['@graph'][0]['screenshot']
    if isinstance(screenshots, str):
        screenshots = [screenshots]
    for image_url in [page.meta['og:image'], page.meta['twitter:image'], data['@graph'][0]['image'], *screenshots]:
        parsed_image = urlsplit(image_url)
        assert parsed_image.netloc=='stpork.github.io' and parsed_image.path.startswith('/mdvu/assets/')
        assert (ROOT / parsed_image.path.lstrip('/')).is_file(), 'Missing SEO image: '+image_url
    if not section:
        assert 'MDVu' in source.split('<h1')[1].split('</h1>')[0]
        assert sum(tag=='details' for tag,_ in page.tags)>=6
    for link in page.links:
        parsed=urlsplit(link)
        if parsed.scheme or parsed.netloc: continue
        if parsed.path:
            target = ROOT / unquote(parsed.path).lstrip('/') if parsed.path.startswith('/') else (ROOT/rel).parent / parsed.path
            if parsed.path.endswith('/'): target /= 'index.html'
            assert target.is_file(), f'{rel}: missing {link}'
            if parsed.fragment and target.suffix == '.html':
                if target not in linked_page_ids: linked_page_ids[target] = Page(target.read_text()).ids
                assert parsed.fragment in linked_page_ids[target], f'{rel}: missing target anchor {link}'
        elif parsed.fragment:
            assert parsed.fragment in page.ids, f'{rel}: missing anchor {link}'
    release = json.loads((ROOT/'mdvu/data/release.json').read_text())
    comparison = json.loads((ROOT/'mdvu/data/comparison.json').read_text())
    if not section:
        assert source.count('macOS · DMG ↓') == 2 and source.count('Windows · MSI ↗') == 2
        assert 'Other versions · portable ZIPs' in source
        assert release['packages']['macos.dmg']['url'] in page.links
        if 'windows-x86_64.msi' in release['packages']:
            assert source.count('href="'+release['packages']['windows-x86_64.msi']['url']+'"') == 2
        assert 'id="comparison"' in source and 'class="landing-table"' in source
        assert source.split('class="landing-table"', 1)[1].split('</thead>', 1)[0].count('<strong>') == 5
        assert source.index('id="comparison"') < source.index('id="why"')
        assert all(p['name'] in source for p in comparison['products'])
        assert ('/mdvu/' + ('ru/' if lang=='ru' else '') + 'performance/') not in page.links
        assert 'Cold &amp; warm starts' not in source and 'comparison-details' not in source
        assert 'N/A' in source
        assert ('>Render · Page</span>' if lang == 'en' else '>Рендер · Страница</span>') in source
        assert ('Formats ↗</a>' if lang == 'en' else 'Форматы ↗</a>') in source
        assert source.index('class="hero-visual"') < source.index('id="comparison"')
    elif section=='performance/':
        assert all(p['name'] in source for p in comparison['products'])
        assert ('Быстродействие' if lang=='ru' else 'Performance') in source
    else:
        cards=[a for tag,a in page.tags if tag=='article' and 'diagram-card' in a.get('class','')]
        assert len(cards)==73
        assert len([a for tag,a in page.tags if tag=='img' and '/diagrams/' in a.get('src','')])==73
        assert 'Source on GitHub' not in source
        assert sum(tag=='a' and 'data-preview' in a for tag,a in page.tags)==73
        assert 'class="image-dialog"' in source
    assert '/mdvu/data/measurements.json' not in page.links
    assert all(removed not in source for removed in ['class="release"', 'class="enlarge"', 'proof-strip', 'size-section', 'measurement-cards', '37 × 2', 'warm scroll', 'тёплый скролл', 'Замеры', 'Less app.', 'Меньше лишнего.'])
    assert (ROOT/rel).stat().st_size < (170000 if section=='diagrams/' else 65000)
    print(f'PASS {rel}: metadata, verification, language links, structured data, internal links, image dimensions')
# Validate the actual search-engine signals together, not just XML syntax.
ORIGIN = 'https://stpork.github.io'
BASE = ORIGIN + '/mdvu'
NS = {'sm':'http://www.sitemaps.org/schemas/sitemap/0.9', 'xhtml':'http://www.w3.org/1999/xhtml'}
variants = {}
expected_pages = {BASE+'/'+s:ROOT/('mdvu/'+s+'index.html') for s in ('','performance/','diagrams/','ru/','ru/performance/','ru/diagrams/')}
robots = RobotFileParser()
robots.parse((ROOT/'robots.txt').read_text().splitlines())
assert ORIGIN+'/sitemap.xml' in (robots.site_maps() or [])
assert robots.can_fetch('Googlebot', ORIGIN+'/sitemap.xml')
sitemap_data = (ROOT/'sitemap.xml').read_bytes()
assert len(sitemap_data) < 50 * 1024 * 1024
sitemap_data.decode('utf-8')
sitemap = ET.fromstring(sitemap_data)
assert sitemap.tag == '{'+NS['sm']+'}urlset'
entries = sitemap.findall('sm:url', NS)
assert 0 < len(entries) <= 50000
listed = [entry.findtext('sm:loc', namespaces=NS) for entry in entries]
assert len(listed) == len(set(listed)), 'Duplicate sitemap URLs'
assert set(listed) == set(expected_pages), 'Only canonical, indexable pages belong in sitemap'
for entry in entries:
    loc = entry.findtext('sm:loc', namespaces=NS)
    parsed = urlsplit(loc)
    assert parsed.scheme == 'https' and parsed.netloc == 'stpork.github.io'
    assert not parsed.query and not parsed.fragment
    date.fromisoformat(entry.findtext('sm:lastmod', namespaces=NS))
    alternate_elements = entry.findall('xhtml:link', NS)
    assert len(alternate_elements) == len(variants)
    assert all(a.get('rel') == 'alternate' for a in alternate_elements)
    alternates = {a.get('hreflang'):a.get('href') for a in alternate_elements}
    assert alternates == variants, 'Incomplete or mismatched sitemap hreflang'
    page = Page(expected_pages[loc].read_text())
    canonical = [a.get('href') for tag,a in page.tags if tag=='link' and a.get('rel')=='canonical']
    assert canonical == [loc], 'Sitemap URL must equal page canonical'
    html_alternates = {a.get('hreflang'):a.get('href') for tag,a in page.tags if tag=='link' and a.get('rel')=='alternate'}
    assert html_alternates == alternates, 'HTML and sitemap hreflang must agree'
    assert robots.can_fetch('Googlebot', loc)
    for directive in ('robots','googlebot'):
        assert 'noindex' not in page.meta.get(directive,'').lower()
print('PASS sitemap: six indexable canonical pages; RU and Performance stay out of the main navigation')
# Old entry points must lead directly to the canonical route, without loops.
for rel,target in [('index.html','/mdvu/'),('ru/index.html','/mdvu/ru/')]:
    source = (ROOT/rel).read_text()
    redirect = Page(source)
    assert redirect.meta['google-site-verification']=='8hoHZ7azFNVSv9x07AUhAS5xpXH3vrk-LlH07z-cgBc'
    canonical = [a.get('href') for tag,a in redirect.tags if tag=='link' and a.get('rel')=='canonical']
    assert canonical == [ORIGIN+target]
    refresh = [a.get('content') for tag,a in redirect.tags if tag=='meta' and a.get('http-equiv')=='refresh']
    assert refresh == ['0;url='+target]
    assert target in redirect.links and 'location.search + location.hash' in source
    assert not any(tag=='h1' for tag,_ in redirect.tags)
    assert robots.can_fetch('Googlebot', ORIGIN+'/'+rel.replace('index.html',''))
    if rel == 'index.html':
        assert ORIGIN+target in expected_pages
    else:
        assert 'noindex' in redirect.meta['robots']
print('PASS migration: root and old Russian URL redirect to canonical pages, verification retained')
assert (ROOT/'mdvu/assets/site.js').stat().st_size < 5500
assert (ROOT/'mdvu/assets/theme.js').stat().st_size < 4000
for platform in ('mac', 'win'):
    assert (ROOT/f'mdvu/assets/mdvu-{platform}.webp').stat().st_size < 200000
    assert (ROOT/f'mdvu/assets/mdvu-{platform}-720.webp').stat().st_size < 80000
print('PASS sitemap and asset budgets')
for doc in ['COMPARISON.md','BENCHMARK-PROTOCOL.md','comparison-history-2026-10-17.md']:
    file = ROOT/'mdvu/data'/doc
    for ref in re.findall(r'\]\(([^)\n]+)\)', file.read_text()):
        parsed = urlsplit(ref)
        if not parsed.scheme and parsed.path:
            assert (file.parent/unquote(parsed.path)).is_file(), f'{doc}: missing document/evidence {ref}'
print('PASS downloadable documentation/evidence links and distinct SEO text')

# A source/error panel or blocked trial must never become a numeric paint result.
performance = json.loads((ROOT/'mdvu/data/performance.json').read_text())
records = performance['measurements']
assert len(records) == 90 and len({x['label'] for x in records}) == 90
assert len(performance['apps']) == 7 and all('Marked' not in a['name'] for a in performance['apps'])
for app in performance['apps']:
    own = [x for x in records if x['app'] == app['name']]
    assert sum(x['group']=='common' for x in own) == 5
    assert sum(x['group']=='original' for x in own) == 5
    assert sum(x['group']=='launch' for x in own) == 1
for row in records:
    assert row['writerDroppedFrames'] == 0
    assert row['memorySamplesAt8s'] >= 3 and row['peakMemoryMiBFirst8s'] >= row['memoryMiBAt8s'] > 0
    assert len(row['sourceSha256']) == 64
    if row['status'] == 'observed':
        lo,hi = row['firstPaintFrameBracketMs']
        # MP4 timebase quantization can shift decoded PTS slightly from the captured timestamp.
        assert 0 <= lo and lo-3 <= row['dispatchToContentMs'] <= hi+3
    else:
        assert row['dispatchToContentMs'] is None and row['launchToContentMs'] is None
assert not list((ROOT/'mdvu').rglob('*.mp4')), 'Test-window recordings must stay local, outside website assets'
print('PASS performance: 90 selections, identical workload counts, frame bounds, memory windows, explicit exclusions')

# Current single-document, cache-cold/warm study: never silently promote pilots.
full = json.loads((ROOT/'mdvu/data/full-pass-performance.json').read_text())
assert len(full['apps']) == 8 and full['plannedAppFixturePhaseCells'] == 192
valid = [m for m in full['measurements'] if m.get('selectedForComparison')]
cells = {(m['app'],m['fixture'],m['cacheState']) for m in valid}
assert len(cells) == len(valid) == full['selectedMeasurementCells']
assert sum(m['eofVerified'] for m in valid)==full['verifiedCanonicalCells']
assert all(m['profileEligible'] and m['singleDocument'] and m['canonicalSeries'] and (m['eofVerified'] or m.get('startupOnlyReview')) and not m['measurementExcluded'] for m in valid)
for m in valid:
    assert m['actualInputSha256'] == m['sourceSha256']
    ram=m['memory']
    assert 0 < ram['medianMiBAt8s'] <= ram['peakMiBFirst8s'] <= ram['peakMiBFullPass']
    timing=m['timing']
    if 'launchToContentMs' in timing:
        assert timing['analysisSchema'] == 7 and timing['launchToContentMs'] > 0
        lo,hi=timing['firstPaintFrameBracketMs']
        assert lo <= timing['dispatchToContentMs'] <= hi+0.001
    if m['cacheState'] == 'warm':assert (m['app'],m['fixture'],'cold') in cells
handled=len(cells)+2*len(full.get('terminalOutcomes',[]))
assert handled==full.get('handledAppFixturePhaseCells',len(cells))
assert full['status'] != 'complete' or handled==192
matrix=json.loads((ROOT/'mdvu/data/diagram-compatibility.json').read_text())
assert matrix['schema']==4 and len(matrix['cases'])==73 and len(matrix['applications'])==8
for app in matrix['applications'].values():
    assert len(app['results'])==73 and sum(app['summary'].values())==73
    assert all(set(c['evidence'])=={'cold','warm'} for c in app['results'].values())
print(f'PASS current study: {len(cells)}/192 verified single-document cells; 584 paired format outcomes')
