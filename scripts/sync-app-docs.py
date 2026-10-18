#!/usr/bin/env python3
"""Copy the local app's versioned comparison evidence and fix download-document links."""
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
ALIASES = {
    'PROTOCOL.md': 'BENCHMARK-PROTOCOL.md',
    'full-pass-2026-10-18.json': 'full-pass-performance.json',
    'application-size-2026-10-18.json': 'application-size.json',
    'diagram-comparison-2026-10-18.json': 'diagram-compatibility.json',
    'diagram-compatibility.json': 'diagram-compatibility-2026-10-17.json',
    'competitor-performance-2026-10-18.json': 'performance.json',
    'mdvu-opening-optimization-2026-10-18.json': 'opening-optimization.json',
    'verification-2026-10-18.json': 'verification.json',
}
LINK = re.compile(r'(\]\()([^\s)]+)(\))')


def sync(source):
    source = source.resolve(strict=True)
    output = ROOT/'mdvu/data'
    copied = set()

    def copy(file):
        file = file.resolve(strict=True)
        if not file.is_relative_to(source):
            raise ValueError('Documentation link leaves app checkout: '+str(file))
        name = ALIASES.get(file.name, file.name)
        if file in copied:
            return name
        copied.add(file)
        if file.suffix == '.md' and 'fixtures' not in file.parts:
            def rewrite(match):
                ref = urlsplit(match[2])
                if ref.scheme or not ref.path:
                    return match[0]
                target = (file.parent/unquote(ref.path)).resolve(strict=True)
                # Original fixtures in the historical report remain repository references.
                if 'fixtures' in target.parts and target.name != 'test-diagrams.md':
                    url = 'https://github.com/stpork/mdvu/blob/develop/'+target.relative_to(source).as_posix()
                else:
                    url = copy(target)
                return match[1]+url+('#'+ref.fragment if ref.fragment else '')+match[3]
            (output/name).write_text(LINK.sub(rewrite, file.read_text()))
        else:
            (output/name).write_bytes(file.read_bytes())
        return name

    copy(source/'COMPARISON.md')
    (ROOT/'mdvu/BENCHMARK-PROTOCOL.md').write_bytes((output/'BENCHMARK-PROTOCOL.md').read_bytes())
    print(f'Synced {len(copied)} documentation/evidence files from {source}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 scripts/sync-app-docs.py /path/to/mdvu')
    sync(Path(sys.argv[1]))
