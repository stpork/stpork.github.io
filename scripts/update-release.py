#!/usr/bin/env python3
"""Snapshot public release assets at build time; no API request in the browser."""
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
REPO = 'https://github.com/stpork/mdvu'


def snapshot(data):
    tag = data['tag_name']
    if data['draft'] or data['prerelease'] or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Expected a public stable release')
    version = tag[1:]
    stable_names = tuple(map(int, version.split('.'))) >= (0, 5, 1)
    packages = {}
    for suffix in ('macos.dmg', 'macos-arm64.zip', 'macos-universal.zip',
                   'macos-x86_64.zip', 'windows-x86_64.msi', 'windows-x86_64.zip'):
        name = f'mdvu-{version}-{suffix}'
        item = next((a for a in data['assets'] if a['name'] == name), None)
        if item is None:
            continue
        url = f'{REPO}/releases/download/{tag}/{name}'
        if item['browser_download_url'] != url or item['size'] <= 0:
            raise ValueError('Invalid release asset: ' + name)
        if stable_names:
            alias_name = f'mdvu-{suffix}'
            alias = next((a for a in data['assets'] if a['name'] == alias_name), None)
            if (alias is None or alias['size'] != item['size']
                    or alias['browser_download_url'] != f'{REPO}/releases/download/{tag}/{alias_name}'
                    or not re.fullmatch(r'sha256:[0-9a-f]{64}', item.get('digest') or '')
                    or alias.get('digest') != item['digest']):
                raise ValueError('Missing or mismatched stable release copy: ' + alias_name)
            url = f'{REPO}/releases/latest/download/{alias_name}'
        packages[suffix] = {'url': url, 'bytes': item['size']}
    if 'macos.dmg' not in packages:
        raise ValueError('Release has no macOS installer')
    if tuple(map(int, version.split('.'))) >= (0, 5, 0) and len(packages) != 6:
        raise ValueError('Release 0.5.0+ must contain all six packages')
    return {'version': version, 'url': f'{REPO}/releases/latest' if stable_names else f'{REPO}/releases/tag/{tag}', 'packages': packages}


if __name__ == '__main__':
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'MDVu-website-build'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = Request('https://api.github.com/repos/stpork/mdvu/releases/latest', headers=headers)
    with urlopen(request, timeout=30) as response:
        release = snapshot(json.load(response))
    (ROOT / 'mdvu/data/release.json').write_text(json.dumps(release, indent=2) + '\n')
    print('Resolved public release ' + release['version'])
