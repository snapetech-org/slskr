#!/usr/bin/env python3
"""Fail a release unless every required stage actually succeeded."""
import json
import os
import sys

REQUIRED = {'version', 'main-ci', 'gate', 'build', 'release', 'downstream-publish', 'discord'}


def incomplete_stages(needs):
    return {name: needs.get(name, {}).get('result', 'missing')
            for name in sorted(REQUIRED)
            if needs.get(name, {}).get('result') != 'success'}


if __name__ == '__main__':
    failures = incomplete_stages(json.loads(os.environ['RELEASE_NEEDS_JSON']))
    if failures:
        for stage, result in failures.items():
            print(f'Required release stage {stage}: {result}', file=sys.stderr)
        sys.exit(1)
    print('Every required build, publisher, and announcement stage succeeded.')
