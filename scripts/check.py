#!/usr/bin/env python3
"""Static release checks for links, localization, metadata and page budgets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
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

for rel,lang in [('mdvu/index.html','en'),('mdvu/ru/index.html','ru')]:
    source = (ROOT/rel).read_text(); page = Page(source)
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
    assert {a.get('hreflang') for tag,a in page.tags if tag=='link' and a.get('rel')=='alternate'} == {'en','ru','x-default'}
    structured = source.split('<script type="application/ld+json">')[1].split('</script>')[0]
    data=json.loads(structured)
    assert data['@graph'][0]['offers']['price']=='0'
    assert data['@graph'][2]['@type']=='WebPage'
    assert data['@graph'][2]['inLanguage']==lang
    canonical_url = 'https://stpork.github.io/mdvu/' + ('ru/' if lang=='ru' else '')
    assert page.meta['og:url']==canonical_url
    assert data['@graph'][0]['url']=='https://stpork.github.io/mdvu/'
    assert data['@graph'][2]['url']==canonical_url
    for image_url in [page.meta['og:image'], page.meta['twitter:image'], data['@graph'][0]['image'], data['@graph'][0]['screenshot']]:
        parsed_image = urlsplit(image_url)
        assert parsed_image.netloc=='stpork.github.io' and parsed_image.path.startswith('/mdvu/assets/')
        assert (ROOT / parsed_image.path.lstrip('/')).is_file(), 'Missing SEO image: '+image_url
    assert 'MDVu' in source.split('<h1')[1].split('</h1>')[0]
    assert sum(tag=='details' for tag,_ in page.tags)>=6
    for link in page.links:
        parsed=urlsplit(link)
        if parsed.scheme or parsed.netloc: continue
        if parsed.path:
            target = ROOT / unquote(parsed.path).lstrip('/') if parsed.path.startswith('/') else (ROOT/rel).parent / parsed.path
            if parsed.path.endswith('/'): target /= 'index.html'
            assert target.is_file(), f'{rel}: missing {link}'
        elif parsed.fragment:
            assert parsed.fragment in page.ids, f'{rel}: missing anchor {link}'
    release = json.loads((ROOT/'mdvu/data/release.json').read_text())
    measured = json.loads((ROOT/'mdvu/data/measurements.json').read_text())
    assert source.count('macOS · DMG ↓') == 2
    assert source.count('Windows · MSI') == 2
    assert '/mdvu/data/measurements.json' in page.links
    assert release['packages']['macos.dmg']['url'] in page.links
    msi = release['packages'].get('windows-x86_64.msi')
    if msi:
        assert msi['url'] in page.links and 'MSI soon' not in source and 'MSI скоро' not in source
    else:
        assert ('MSI soon' if lang == 'en' else 'MSI скоро') in source
        assert not any('/releases/download/' in link and link.endswith('.msi') for link in page.links)
    assert all(a['name'] in source for a in measured['packages'])
    assert len(measured['fixtures']) == 74 and len(measured['warmScrolling']) == 74
    for platform in ['macos','windows']:
        assert len([f for f in measured['fixtures'] if f['platform'] == platform]) == 37
        for phase in ['before','after']:
            intervals = sorted(v for f in measured['warmScrolling'] if f['platform'] == platform
                               for values in f[phase]['frames'][1:] for v in values)
            assert len(intervals) == 37 * 120
            assert round(intervals[int(len(intervals)*.95)], 1) == measured['summary'][platform][phase]['warmP95Ms']
    assert all(old not in source for old in ['cmark-gfm', '61.57', '~3.4'])
    assert (ROOT/rel).stat().st_size < 50000
    print(f'PASS {rel}: metadata, verification, language links, structured data, internal links, image dimensions')
# Validate the actual search-engine signals together, not just XML syntax.
ORIGIN = 'https://stpork.github.io'
BASE = ORIGIN + '/mdvu'
NS = {'sm':'http://www.sitemaps.org/schemas/sitemap/0.9', 'xhtml':'http://www.w3.org/1999/xhtml'}
variants = {'en':BASE+'/', 'ru':BASE+'/ru/', 'x-default':BASE+'/'}
expected_pages = {BASE+'/':ROOT/'mdvu/index.html', BASE+'/ru/':ROOT/'mdvu/ru/index.html'}
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
print('PASS sitemap: canonical pages, reciprocal hreflang, valid dates and robots access')
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
    assert ORIGIN+target in expected_pages
print('PASS migration: root and old Russian URL redirect to canonical pages, verification retained')
assert (ROOT/'mdvu/assets/site.js').stat().st_size < 5000
assert (ROOT/'mdvu/assets/theme.js').stat().st_size < 4000
assert (ROOT/'mdvu/assets/mdvu.webp').stat().st_size < 150000
print('PASS sitemap and asset budgets')
