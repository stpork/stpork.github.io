#!/usr/bin/env python3
"""Static release checks for links, localization, metadata and page budgets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
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
    assert 'class="language"' not in source if lang=='en' else 'hreflang="en">EN</a>' in source
    assert {a.get('hreflang') for tag,a in page.tags if tag=='link' and a.get('rel')=='alternate'} == {'en','ru','x-default'}
    structured = source.split('<script type="application/ld+json">')[1].split('</script>')[0]
    data=json.loads(structured)
    assert data['@graph'][0]['offers']['price']=='0'
    assert data['@graph'][2]['@type']=='WebPage'
    assert data['@graph'][2]['inLanguage']==lang
    assert 'MDVu' in source.split('<h1')[1].split('</h1>')[0]
    assert sum(tag=='details' for tag,_ in page.tags)==6
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
ET.parse(ROOT/'sitemap.xml')
assert (ROOT/'assets/site.js').stat().st_size < 5000
assert (ROOT/'assets/mdvu.webp').stat().st_size < 150000
print('PASS sitemap and asset budgets')
