#!/usr/bin/env python3
"""Wait for public package publication. Never upload, retry, or send messages."""
import argparse
import datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


CHROOTS = {'fedora-43-x86_64', 'fedora-43-aarch64',
           'fedora-rawhide-x86_64', 'fedora-rawhide-aarch64'}
PPA = 'https://api.launchpad.net/1.0/~keefshape/+archive/ubuntu/slskdn'
APT = 'https://ppa.launchpadcontent.net/keefshape/slskdn/ubuntu/'
COPR = 'https://copr.fedorainfracloud.org/api_3/'
RPM = 'https://download.copr.fedorainfracloud.org/results/slskdn/slskr/'
NS = {'r': 'http://linux.duke.edu/metadata/repo',
      'p': 'http://linux.duke.edu/metadata/common'}


def read(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'slskr-publication-check'})
    with urllib.request.urlopen(request, timeout=25) as response:
        data = response.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise ValueError('repository metadata exceeds size limit')
    return data


def public_file(url):
    with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=25) as response:
        if response.status != 200:
            raise ValueError('package is not publicly downloadable')


def gunzip(data):
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
        result = stream.read(32 * 1024 * 1024 + 1)
    if len(result) > 32 * 1024 * 1024:
        raise ValueError('uncompressed repository metadata exceeds size limit')
    return result


def relative_url(base, path):
    url = urllib.parse.urljoin(base, path)
    if not url.startswith(base) or '..' in urllib.parse.unquote(path).split('/'):
        raise ValueError('package location escapes its public repository')
    return url


def json_read(url):
    return json.loads(read(url))


def copr(version):
    rows = json_read(COPR + 'build/list?ownername=slskdn&projectname=slskr&limit=100')['items']
    builds = [b for b in rows if (b.get('source_package') or {}).get('version') == version + '-1']
    if not builds:
        raise ValueError('COPR release build not found')
    build = builds[0]
    chroots = json_read(COPR + 'build-chroot/list?build_id=' + str(build['id']))['items']
    if (build['state'] != 'succeeded' or {c['name'] for c in chroots} != CHROOTS
            or any(c['state'] != 'succeeded' for c in chroots)):
        raise ValueError('COPR native builds are not all successful')
    packages = {}
    for chroot in sorted(CHROOTS):
        base = RPM + chroot + '/'
        index = ET.fromstring(read(base + 'repodata/repomd.xml'))
        primary = next(n for n in index.findall('r:data', NS) if n.attrib['type'] == 'primary')
        href = primary.find('r:location', NS).attrib['href']
        compressed = read(relative_url(base, href))
        checksum = primary.find('r:checksum', NS)
        if checksum.attrib['type'] != 'sha256' or hashlib.sha256(compressed).hexdigest() != checksum.text:
            raise ValueError('COPR repository metadata checksum mismatch')
        if not href.endswith('.gz'):
            raise ValueError('unsupported COPR primary metadata encoding')
        entries = ET.fromstring(gunzip(compressed)).findall('p:package', NS)
        matching = [p for p in entries if p.findtext('p:name', namespaces=NS) == 'slskr'
                    and p.find('p:version', NS).attrib['ver'] == version
                    and chroot.endswith('-' + p.findtext('p:arch', namespaces=NS))]
        if not matching:
            raise ValueError('COPR public index is missing ' + chroot)
        url = relative_url(base, matching[0].find('p:location', NS).attrib['href'])
        public_file(url)
        packages[chroot] = url
    return {'build': build['id'], 'packages': packages}


def ppa(version):
    sources = json_read(PPA + '?ws.op=getPublishedSources&source_name=slskr&exact_match=true&status=Published')['entries']
    sources = [s for s in sources if s['source_package_version'].startswith(version + '-')]
    if not sources:
        raise ValueError('Launchpad release source is not published')
    source = sources[0]
    # Only follow links in the configured archive, including links from its API.
    builds_url = relative_url(PPA + '/', source['self_link']) + '?ws.op=getBuilds'
    builds = json_read(builds_url)['entries']
    if not builds or any(b['buildstate'] != 'Successfully built' for b in builds):
        raise ValueError('Launchpad binary builds are still queued or unsuccessful')
    architectures = {b['arch_tag'] for b in builds}
    if 'amd64' not in architectures:
        raise ValueError('Launchpad is missing its required amd64 build')
    packages = {}
    for arch in sorted(architectures):
        if arch not in ('amd64', 'arm64'):
            raise ValueError('unexpected Launchpad architecture')
        url = APT + f'dists/jammy/main/binary-{arch}/Packages.gz?fresh={int(time.time())}'
        blocks = gunzip(read(url)).decode().strip().split('\n\n')
        rows = [dict(line.split(': ', 1) for line in block.splitlines()
                     if ': ' in line and not line.startswith(' ')) for block in blocks]
        rows = [r for r in rows if r.get('Package') == 'slskr'
                and r.get('Version') == source['source_package_version'] and r.get('Architecture') == arch]
        if not rows or not re.fullmatch('[0-9a-f]{64}', rows[0].get('SHA256', '')):
            raise ValueError('Launchpad binary is missing from the public apt index: ' + arch)
        package = relative_url(APT, rows[0]['Filename'])
        public_file(package)
        packages[arch] = {'url': package, 'sha256': rows[0]['SHA256']}
    return {'version': source['source_package_version'], 'packages': packages}


def winget(version, windows_sha):
    url = ('https://raw.githubusercontent.com/microsoft/winget-pkgs/master/'
           f'manifests/s/snapetech/slskr/{version}/snapetech.slskr.installer.yaml')
    manifest = read(url).decode()
    package_version = re.search(r'^PackageVersion:\s*[\'"]?([^\s\'"\r\n]+)', manifest, re.M)
    hashes = re.findall(r'^\s+InstallerSha256:\s*([0-9a-fA-F]{64})\s*$', manifest, re.M)
    if not package_version or package_version[1] != version or [s.lower() for s in hashes] != [windows_sha]:
        raise ValueError('public Winget manifest does not match the release archive')
    return {'manifest': url, 'windowsSha256': windows_sha}


def chocolatey(version, allow_initial_review=False):
    if allow_initial_review:
        first = "https://community.chocolatey.org/api/v2/Packages(Id='slskr',Version='0.2.82')"
        values = {n.tag.split('}')[-1]: n.text for n in ET.fromstring(read(first)).iter()}
        if values.get('Version') == '0.2.82' and values.get('IsApproved') == 'false':
            return {'publicationStatus': 'pending-initial-review', 'authorizedDeferral': True,
                    'firstPackage': first, 'requestedVersion': version, 'published': False}
    url = f"https://community.chocolatey.org/api/v2/Packages(Id='slskr',Version='{version}')"
    xml = ET.fromstring(read(url))
    values = {n.tag.split('}')[-1]: n.text for n in xml.iter()}
    if values.get('Version') != version or values.get('IsApproved') != 'true':
        raise ValueError('Chocolatey release package has not been approved')
    return {'package': url, 'version': version, 'approved': True}


def snapshot(probes, previous=None):
    states = dict(previous or {})
    for name, probe in probes.items():
        if (states.get(name, {}).get('ready')
                or states.get(name, {}).get('evidence', {}).get('authorizedDeferral')):
            continue
        try:
            evidence = probe()
            states[name] = {'ready': not evidence.get('authorizedDeferral', False), 'evidence': evidence}
        except Exception as exc:
            states[name] = {'ready': False, 'reason': str(exc)}
    return states


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag')
    parser.add_argument('--wait-seconds', type=int, default=0)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--allow-chocolatey-initial-review', action='store_true',
                        help='Owner-authorized pending exception; never reports Chocolatey as published')
    args = parser.parse_args()
    match = re.fullmatch(r'(?:release-)?v([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)', args.tag)
    if not match or not 0 <= args.wait_seconds <= 5400:
        parser.error('expected a release tag and a wait between 0 and 5400 seconds')
    version = match[1]
    sums = read(f'https://github.com/snapetech-org/slskr/releases/download/{args.tag}/SHA256SUMS.txt').decode()
    archive = 'slskr-v' + version + '-x86_64-pc-windows-msvc.zip'
    hashes = re.findall(r'^([0-9a-fA-F]{64})\s+\*?(?:\./)?' + re.escape(archive) + r'\s*$', sums, re.M)
    if len(hashes) != 1:
        raise ValueError('release checksum manifest must contain exactly one Windows archive')
    probes = {'copr': lambda: copr(version), 'launchpad': lambda: ppa(version),
              'winget': lambda: winget(version, hashes[0].lower()),
              'chocolatey': lambda: chocolatey(version, args.allow_chocolatey_initial_review)}
    deadline = time.monotonic() + args.wait_seconds
    states = {}
    while True:
        states = snapshot(probes, states)
        complete = all(s['ready'] for s in states.values())
        deferred = [name for name, state in states.items() if state.get('evidence', {}).get('authorizedDeferral')]
        required_available = all(s['ready'] or name in deferred for name, s in states.items())
        receipt = {'tag': args.tag, 'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'complete': complete, 'requiredChannelsAvailable': required_available,
                   'authorizedDeferrals': deferred, 'channels': states}
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt), flush=True)
        if required_available:
            return 0
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 1
        time.sleep(min(60, remaining))


if __name__ == '__main__':
    raise SystemExit(main())
