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

for rel,lang in [('index.html','en'),('ru/index.html','ru')]:
    source = (ROOT/rel).read_text(); page = Page(source)
    assert source.startswith('<!doctype html>')
    assert f'<html lang="{lang}">' in source
    assert sum(tag=='h1' for tag,_ in page.tags)==1
    assert page.meta['google-site-verification']=='8hoHZ7azFNVSv9x07AUhAS5xpXH3vrk-LlH07z-cgBc'
    assert source.index('google-site-verification') < source.index('</head>') < source.index('<body>')
    assert 90 <= len(page.meta['description']) <= 180
    assert page.meta['twitter:card']=='summary_large_image'
    assert page.meta['color-scheme']=='light dark'
    assert source.index('/assets/theme.js') < source.index('/assets/site.css')
    assert sum(tag=='button' and 'data-theme-toggle' in attrs for tag,attrs in page.tags)==1
    assert 'class="language"' not in source if lang=='en' else 'hreflang="en">EN</a>' in source
    assert {a.get('hreflang') for tag,a in page.tags if tag=='link' and a.get('rel')=='alternate'} == {'en','ru','x-default'}
    structured = source.split('<script type="application/ld+json">')[1].split('</script>')[0]
    data=json.loads(structured)
    assert data['@graph'][0]['offers']['price']=='0'
    assert data['@graph'][2]['@type']=='WebPage'
    assert data['@graph'][2]['inLanguage']==lang
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
    assert (ROOT/rel).stat().st_size < 50000
    print(f'PASS {rel}: metadata, verification, language links, structured data, internal links, image dimensions')
# Validate the actual search-engine signals together, not just XML syntax.
BASE = 'https://stpork.github.io'
NS = {'sm':'http://www.sitemaps.org/schemas/sitemap/0.9', 'xhtml':'http://www.w3.org/1999/xhtml'}
variants = {'en':BASE+'/', 'ru':BASE+'/ru/', 'x-default':BASE+'/'}
expected_pages = {BASE+'/':ROOT/'index.html', BASE+'/ru/':ROOT/'ru/index.html'}
robots = RobotFileParser()
robots.parse((ROOT/'robots.txt').read_text().splitlines())
assert BASE+'/sitemap.xml' in (robots.site_maps() or [])
assert robots.can_fetch('Googlebot', BASE+'/sitemap.xml')
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
assert (ROOT/'assets/site.js').stat().st_size < 5000
assert (ROOT/'assets/theme.js').stat().st_size < 4000
assert (ROOT/'assets/mdvu.webp').stat().st_size < 150000
print('PASS sitemap and asset budgets')
