import importlib.util
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
import build

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('update-release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def data(self, version):
        suffixes = ['macos.dmg', 'macos-arm64.zip', 'macos-universal.zip', 'macos-x86_64.zip']
        if tuple(map(int, version.split('.'))) >= (0, 5, 0):
            suffixes += ['windows-x86_64.msi', 'windows-x86_64.zip']
        assets = [
            {'name': f'mdvu-{version}-{suffix}', 'size': 100,
             'digest': 'sha256:' + hashlib.sha256(suffix.encode()).hexdigest(),
             'browser_download_url': f'{release.REPO}/releases/download/v{version}/mdvu-{version}-{suffix}'}
            for suffix in suffixes]
        if tuple(map(int, version.split('.'))) >= (0, 5, 1):
            assets += [dict(item, name=item['name'].replace(version+'-', ''),
                            browser_download_url=item['browser_download_url'].replace('/mdvu-'+version+'-', '/mdvu-'))
                       for item in assets[:]]
        return {'tag_name': 'v'+version, 'draft': False, 'prerelease': False, 'assets': assets}

    def test_old_release_does_not_invent_windows_downloads(self):
        result = release.snapshot(self.data('0.4.1'))
        self.assertNotIn('windows-x86_64.msi', result['packages'])

    def test_complete_release_resolves_all_six(self):
        for version in ('0.5.0', '0.5.1'):
            with self.subTest(version=version):
                result = release.snapshot(self.data(version))
                self.assertEqual(len(result['packages']), 6)
                self.assertTrue(result['packages']['windows-x86_64.msi']['url'].endswith('.msi'))

    def test_new_release_must_be_complete(self):
        data = self.data('0.5.0'); data['assets'].pop()
        with self.assertRaises(ValueError):
            release.snapshot(data)

    def test_rejects_draft_and_foreign_download_url(self):
        data = self.data('0.5.0'); data['draft'] = True
        with self.assertRaises(ValueError):
            release.snapshot(data)
        data['draft'] = False; data['assets'][0]['browser_download_url'] = 'https://example.com/fake.dmg'
        with self.assertRaises(ValueError):
            release.snapshot(data)

    def test_future_releases_keep_the_same_latest_download_urls(self):
        current, future = [release.snapshot(self.data(v)) for v in ('0.5.1', '1.2.3')]
        self.assertEqual(current['packages'], future['packages'])
        self.assertEqual(current['url'], release.REPO + '/releases/latest')
        self.assertEqual(current['packages']['macos.dmg']['url'],
                         release.REPO + '/releases/latest/download/mdvu-macos.dmg')

    def test_latest_copies_must_match_original_release_assets(self):
        for field, value in [('size', 99), ('digest', 'sha256:'+'0'*64),
                             ('browser_download_url', 'https://example.com/fake.dmg')]:
            with self.subTest(field=field):
                data = self.data('0.5.1')
                data['assets'][6][field] = value
                with self.assertRaisesRegex(ValueError, 'stable release copy'):
                    release.snapshot(data)
        data = self.data('0.5.1'); data['assets'].pop()
        with self.assertRaisesRegex(ValueError, 'stable release copy'):
            release.snapshot(data)


class DownloadButtonsTests(unittest.TestCase):
    def test_latest_downloads_and_faq_do_not_need_version_edits(self):
        prefix = release.REPO + '/releases/latest/download/mdvu'
        mac, windows = prefix + '-macos.dmg', prefix + '-windows-x86_64.msi'
        for version in ('0.5.1', '1.2.3'):
            with patch.dict(build.page.__globals__, VERSION=version, DOWNLOAD=mac, WINDOWS=windows):
                for lang in ('en', 'ru'):
                    with self.subTest(lang=lang, version=version):
                        html = build.page(lang)
                        self.assertIn(f'"softwareVersion":"{version}"', html)
                        self.assertIn(release.REPO + '/releases/latest', html)
                        self.assertEqual(html.count(f'href="{mac}" download'), 2)
                        self.assertEqual(html.count(f'href="{windows}" download'), 2)
                        self.assertNotIn('/releases/download/v', html)
                        self.assertIn('latest stable release' if lang == 'en' else 'последний стабильный релиз', html)

    def test_hero_links_to_releases_and_does_not_invent_msi(self):
        with patch.dict(build.page.__globals__, WINDOWS=None):
            for lang in ['en', 'ru']:
                html = build.page(lang)
                self.assertEqual(html.count('macOS · DMG ↓'), 2)
                self.assertEqual(html.count('Windows · MSI ↗'), 2)
                self.assertIn('Other versions · portable ZIPs', html)
                self.assertNotIn('MSI soon', html)
                self.assertNotIn('MSI скоро', html)
                self.assertNotIn('href="https://github.com/stpork/mdvu/releases/download/v0.5.0/mdvu-0.5.0-windows-x86_64.msi"', html)

    def test_published_msi_is_in_installation_section(self):
        url = release.REPO + '/releases/download/v0.5.0/mdvu-0.5.0-windows-x86_64.msi'
        with patch.dict(build.page.__globals__, WINDOWS=url, VERSION='0.5.0'):
            for lang in ['en', 'ru']:
                html = build.page(lang)
                self.assertEqual(html.count(f'href="{url}" download'), 2)
                self.assertEqual(html.count('Windows · MSI ↓'), 2)
                self.assertEqual(html.count(f'href="{build.DOWNLOAD}" download'), 2)

    def test_direct_url_pages_are_indexable_without_navigation_links(self):
        en, ru = build.page('en'), build.page('ru')
        self.assertNotIn('/mdvu/ru/', en)
        self.assertNotIn('hreflang="ru"', en + ru)
        self.assertIn('content="index, follow, max-image-preview:large"', ru)
        for lang in ['en','ru']:
            self.assertNotIn('noindex', build.page(lang, 'performance'))
            self.assertNotIn('href="/mdvu/performance/"', build.page('en'))
        self.assertNotIn('content="noindex, follow"', en)
