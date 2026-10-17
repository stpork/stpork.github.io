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
        if version == '0.5.0':
            suffixes += ['windows-x86_64.msi', 'windows-x86_64.zip']
        return {'tag_name': 'v'+version, 'draft': False, 'prerelease': False, 'assets': [
            {'name': f'mdvu-{version}-{suffix}', 'size': 100,
             'browser_download_url': f'{release.REPO}/releases/download/v{version}/mdvu-{version}-{suffix}'}
            for suffix in suffixes]}

    def test_old_release_does_not_invent_windows_downloads(self):
        result = release.snapshot(self.data('0.4.1'))
        self.assertNotIn('windows-x86_64.msi', result['packages'])

    def test_complete_release_resolves_all_six(self):
        result = release.snapshot(self.data('0.5.0'))
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
    def test_hero_links_to_releases_and_does_not_invent_msi(self):
        with patch.dict(build.page.__globals__, WINDOWS=None):
            for lang in ['en', 'ru']:
                html = build.page(lang)
                self.assertIn('>GitHub Releases ↗</a>', html)
                self.assertNotIn('MSI soon', html)
                self.assertNotIn('MSI скоро', html)
                self.assertNotIn('href="https://github.com/stpork/mdvu/releases/download/v0.5.0/mdvu-0.5.0-windows-x86_64.msi"', html)

    def test_published_msi_is_in_installation_section(self):
        url = release.REPO + '/releases/download/v0.5.0/mdvu-0.5.0-windows-x86_64.msi'
        with patch.dict(build.page.__globals__, WINDOWS=url, VERSION='0.5.0'):
            for lang in ['en', 'ru']:
                self.assertEqual(build.page(lang).count(f'href="{url}"'), 1)

    def test_russian_is_not_advertised_or_indexable(self):
        en, ru = build.page('en'), build.page('ru')
        self.assertNotIn('/mdvu/ru/', en)
        self.assertNotIn('hreflang="ru"', en + ru)
        self.assertIn('content="noindex, follow"', ru)
        self.assertNotIn('content="noindex, follow"', en)
