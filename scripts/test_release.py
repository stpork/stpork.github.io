import importlib.util
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
        return {'tag_name': 'v'+version, 'draft': False, 'prerelease': False, 'assets': [
            {'name': f'mdvu-{version}-{suffix}', 'size': 100,
             'browser_download_url': f'{release.REPO}/releases/download/v{version}/mdvu-{version}-{suffix}'}
            for suffix in suffixes]}

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


class DownloadButtonsTests(unittest.TestCase):
    def test_patch_release_updates_downloads_faq_and_search_metadata(self):
        version = '0.5.1'
        prefix = release.REPO + '/releases/download/v' + version + '/mdvu-' + version
        mac, windows = prefix + '-macos.dmg', prefix + '-windows-x86_64.msi'
        with patch.dict(build.page.__globals__, VERSION=version, DOWNLOAD=mac, WINDOWS=windows):
            for lang in ('en', 'ru'):
                with self.subTest(lang=lang):
                    html = build.page(lang)
                    self.assertIn('"softwareVersion":"0.5.1"', html)
                    self.assertIn(release.REPO + '/releases/tag/v0.5.1', html)
                    self.assertEqual(html.count(f'href="{mac}" download'), 2)
                    self.assertEqual(html.count(f'href="{windows}" download'), 2)
                    self.assertNotIn('/releases/download/v0.5.0/', html)
                    self.assertIn('The current release is 0.5.1.' if lang == 'en' else 'Текущий релиз — 0.5.1.', html)

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
