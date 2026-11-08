#!/usr/bin/env python3
"""Public catalog fixtures: submission acceptance must not imply publication."""
import gzip
import hashlib
import importlib.util
import io
import json
import contextlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

SPEC = importlib.util.spec_from_file_location('publication', Path(__file__).with_name('check-public-release.py'))
publication = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def test_http_transport_rejects_local_files_and_untrusted_redirects(self):
        def client():
            session = MagicMock()
            session.__enter__.return_value = session
            return session
        for url in ('file:///etc/passwd', 'http://github.com/package',
                    'https://localhost/package', 'https://github.com:8443/package',
                    'https://user:password@github.com/package', 'https://@github.com/package'):
            session = client()
            with self.subTest(url=url), patch.object(publication, 'public_session', return_value=session):
                with self.assertRaises(ValueError):
                    publication.read(url)
                session.request.assert_not_called()
        response = Mock(status_code=302, headers={'Location': 'https://localhost/package'})
        session = client()
        session.request.return_value.__enter__.return_value = response
        with patch.object(publication, 'public_session', return_value=session):
            with self.assertRaises(ValueError):
                publication.read('https://github.com/package')
            self.assertEqual(session.request.call_count, 1)
        redirect = Mock(status_code=302, headers={'Location': 'https://packages.redhat.com/package'})
        content = Mock(status_code=200)
        content.iter_content.return_value = [b'public metadata']
        session = client()
        session.request.return_value.__enter__.side_effect = [redirect, content]
        with patch.object(publication, 'public_session', return_value=session):
            self.assertEqual(publication.read(publication.RPM + 'package'), b'public metadata')
            self.assertEqual(session.request.call_count, 2)
            for call in session.request.call_args_list:
                self.assertTrue(call.kwargs['verify'])
                self.assertFalse(call.kwargs['allow_redirects'])

    def test_authorized_review_exception_is_not_reported_as_complete_publication(self):
        with tempfile.TemporaryDirectory(prefix='slskr-publication-test-') as directory:
            receipt = Path(directory) / 'receipt.json'
            arguments = ['check-public-release.py', 'v0.2.84', '--receipt', str(receipt),
                         '--allow-chocolatey-initial-review']
            checksum = ('a' * 64 + '  ./slskr-v0.2.84-x86_64-pc-windows-msvc.zip\n').encode()
            first = b'<entry><Version>0.2.82</Version><IsApproved>false</IsApproved></entry>'
            with patch('sys.argv', arguments), patch.object(publication, 'read', side_effect=[checksum, first]), \
                 patch.object(publication, 'copr', return_value={'build': 123}), \
                 patch.object(publication, 'ppa', return_value={'package': 'public'}), \
                 patch.object(publication, 'winget', return_value={'manifest': 'public'}), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(publication.main(), 0)
            result = json.loads(receipt.read_text())
            self.assertFalse(result['complete'])
            self.assertTrue(result['requiredChannelsAvailable'])
            self.assertEqual(result['authorizedDeferrals'], ['chocolatey'])
            self.assertFalse(result['channels']['chocolatey']['ready'])

    def test_completed_channels_are_cached_but_pending_channels_are_rechecked(self):
        ready = Mock(return_value={'package': 'public'})
        pending = Mock(side_effect=[ValueError('queued'), {'package': 'public'}])
        states = publication.snapshot({'ready': ready, 'pending': pending})
        self.assertFalse(states['pending']['ready'])
        states = publication.snapshot({'ready': ready, 'pending': pending}, states)
        self.assertTrue(all(s['ready'] for s in states.values()))
        self.assertEqual(ready.call_count, 1)
        self.assertEqual(pending.call_count, 2)

    def test_chocolatey_requires_approval_unless_initial_review_is_explicitly_allowed(self):
        def feed(version, approved):
            return f'<entry><properties><Version>{version}</Version><IsApproved>{approved}</IsApproved></properties></entry>'.encode()
        with patch.object(publication, 'read', return_value=feed('0.2.84', 'false')):
            with self.assertRaises(ValueError):
                publication.chocolatey('0.2.84')
        with patch.object(publication, 'read', return_value=feed('0.2.84', 'true')):
            self.assertTrue(publication.chocolatey('0.2.84')['approved'])
        with patch.object(publication, 'read', return_value=feed('0.2.82', 'false')) as read:
            deferred = publication.chocolatey('0.2.84', allow_initial_review=True)
            self.assertFalse(deferred['published'])
            self.assertTrue(deferred['authorizedDeferral'])
            self.assertEqual(read.call_count, 1)
            states = publication.snapshot({'chocolatey': lambda: deferred})
            self.assertFalse(states['chocolatey']['ready'])
        with patch.object(publication, 'read', side_effect=[feed('0.2.82', 'true'), feed('0.2.84', 'false')]):
            with self.assertRaises(ValueError):
                publication.chocolatey('0.2.84', allow_initial_review=True)

    def test_winget_requires_merged_version_and_the_exact_windows_archive(self):
        for version, digest, valid in (('0.2.84', 'a' * 64, True),
                                       ('0.2.83', 'a' * 64, False),
                                       ('0.2.84', 'b' * 64, False)):
            with self.subTest(version=version, digest=digest):
                data = f'PackageVersion: {version}\nInstallers:\n- Architecture: x64\n  InstallerSha256: {digest}\n'.encode()
                with patch.object(publication, 'read', return_value=data) as read:
                    if valid:
                        publication.winget('0.2.84', 'a' * 64)
                    else:
                        with self.assertRaises(ValueError):
                            publication.winget('0.2.84', 'a' * 64)
                    self.assertIn('/master/', read.call_args.args[0])

    def test_launchpad_source_or_successful_build_alone_is_insufficient(self):
        source = {'source_package_version': '0.2.84-1ppa123~jammy',
                  'self_link': publication.PPA + '/+sourcepub/123'}
        for state, apt_version, valid in (('Needs building', '0.2.84-1ppa123~jammy', False),
                                           ('Successfully built', '0.2.83-1ppa100~jammy', False),
                                           ('Successfully built', '0.2.84-1ppa123~jammy', True)):
            with self.subTest(state=state, apt_version=apt_version):
                replies = [{'entries': [source]}, {'entries': [{'buildstate': state, 'arch_tag': 'amd64'}]}]
                index = gzip.compress(f'Package: slskr\nVersion: {apt_version}\nArchitecture: amd64\nFilename: pool/main/s/slskr/package.deb\nSHA256: {"a" * 64}\n'.encode())
                with patch.object(publication, 'json_read', side_effect=replies), \
                     patch.object(publication, 'read', return_value=index), \
                     patch.object(publication, 'public_file') as public:
                    if valid:
                        result = publication.ppa('0.2.84')
                        self.assertIn('amd64', result['packages'])
                        public.assert_called_once()
                    else:
                        with self.assertRaises(ValueError):
                            publication.ppa('0.2.84')
                        public.assert_not_called()

    def test_copr_requires_all_native_builds_and_public_indexes(self):
        build = {'id': 123, 'state': 'succeeded', 'source_package': {'version': '0.2.84-1'}}
        chroots = [{'name': name, 'state': 'succeeded'} for name in publication.CHROOTS]
        data = {}
        for chroot in publication.CHROOTS:
            arch = chroot.rsplit('-', 1)[1]
            primary = gzip.compress((f'<metadata xmlns="{publication.NS["p"]}"><package>'
                                     f'<name>slskr</name><arch>{arch}</arch><version ver="0.2.84"/>'
                                     '<location href="Packages/s/package.rpm"/></package></metadata>').encode())
            index = (f'<repomd xmlns="{publication.NS["r"]}"><data type="primary">'
                     '<location href="repodata/primary.xml.gz"/><checksum type="sha256">'
                     f'{hashlib.sha256(primary).hexdigest()}</checksum></data></repomd>').encode()
            base = publication.RPM + chroot + '/'
            data[base + 'repodata/repomd.xml'] = index
            data[base + 'repodata/primary.xml.gz'] = primary
        for missing in (False, True):
            with self.subTest(missing_architecture=missing):
                replies = [{'items': [build]}, {'items': chroots[:-1] if missing else chroots}]
                with patch.object(publication, 'json_read', side_effect=replies), \
                     patch.object(publication, 'read', side_effect=lambda url: data[url]), \
                     patch.object(publication, 'public_file') as public:
                    if missing:
                        with self.assertRaises(ValueError):
                            publication.copr('0.2.84')
                        public.assert_not_called()
                    else:
                        self.assertEqual(len(publication.copr('0.2.84')['packages']), 4)
                        self.assertEqual(public.call_count, 4)

    def test_untrusted_repository_locations_cannot_escape(self):
        for path in ('https://example.com/package', '../package', '%2e%2e/package'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                publication.relative_url(publication.APT, path)


if __name__ == '__main__':
    unittest.main()
