#!/usr/bin/env python3
"""Announce a published release and retain Discord's message confirmation."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse

from discord_release_route import publish


def build_payload(release, tag, repository, workflow_url, *, truncate=True):
    if not re.fullmatch(r'(?:release-)?v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?', tag):
        raise ValueError('Release tag must use v<semver> or release-v<semver>.')
    url = f'https://github.com/{repository}/releases/tag/{tag}'
    if release.get('tagName') != tag or release.get('url') != url:
        raise ValueError('Published release does not match the requested repository and tag.')
    if release.get('isDraft') or not release.get('publishedAt'):
        raise ValueError('Only published releases may be announced.')
    body = (release.get('body') or '').strip()
    if not body:
        raise ValueError('Release notes must be nonempty.')
    body += '\n\nRelease artifacts are available on GitHub.'
    # Discord limits embed descriptions; preserve whole Unicode characters.
    if truncate and len(body.encode('utf-16-le')) > 7600:
        body = body.encode('utf-16-le')[:7594].decode('utf-16-le', errors='ignore') + '…'
    version = tag.removeprefix('release-').removeprefix('v')
    return {
        'username': 'slskr Releases',
        'allowed_mentions': {'parse': []},
        'embeds': [{
            'title': f'slskr {version} is live', 'url': url, 'description': body,
            'fields': [
                {'name': 'Tag', 'value': tag, 'inline': True},
                {'name': 'Workflow', 'value': workflow_url, 'inline': True},
            ],
        }],
    }


def execute_webhook(webhook, payload):
    parsed = urllib.parse.urlsplit(webhook)
    if (parsed.scheme != 'https' or parsed.hostname not in {'discord.com', 'discordapp.com'}
            or parsed.username or parsed.password or parsed.port not in {None, 443}
            or not re.fullmatch(r'/api/(?:v[0-9]+/)?webhooks/[0-9]+/[^/]+/?', parsed.path)):
        raise ValueError('Configure a Discord HTTPS webhook in DISCORD_RELEASE_WEBHOOK_URL.')
    query = [(key, value) for key, value in urllib.parse.parse_qsl(parsed.query) if key != 'wait']
    query.append(('wait', 'true'))
    url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query), fragment=''))
    try:
        response = subprocess.run([
            'curl', '--silent', '--show-error', '--max-time', '30',
            '--proto', '=https', '--request', 'POST',
            '--header', 'Content-Type: application/json',
            '--user-agent', 'DiscordBot (https://github.com/snapetech-org/slskr, 1.0)',
            '--data-binary', '@-', '--write-out', '\n%{http_code}', url,
        ], input=json.dumps(payload), capture_output=True, text=True, timeout=35, check=False)
        if response.returncode:
            raise RuntimeError('Discord delivery was not confirmed; inspect the channel before retrying.')
        body, status = response.stdout.rsplit('\n', 1)
        if status != '200':
            raise RuntimeError(f'Discord returned HTTP {status}; inspect the channel before retrying.')
        message = json.loads(body)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise RuntimeError('Discord delivery was not confirmed; inspect the channel before retrying.') from None
    if (not isinstance(message, dict) or not str(message.get('id', '')).isdecimal()
            or not str(message.get('channel_id', '')).isdecimal()):
        raise RuntimeError('Discord returned no message confirmation; inspect the channel before retrying.')
    return {'message_id': str(message['id']), 'channel_id': str(message['channel_id']),
            'release_url': payload['embeds'][0]['url']}


def main():
    release_path, receipt_path = map(Path, sys.argv[1:])
    repository = os.environ['GITHUB_REPOSITORY']
    tag = os.environ['RELEASE_TAG']
    workflow_url = f"https://github.com/{repository}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    changelog = os.environ.get('DISCORD_CHANGELOG_WEBHOOK', '')
    project = os.environ.get('DISCORD_RELEASE_WEBHOOK_URL', '')
    payload = build_payload(json.loads(release_path.read_text()), tag, repository, workflow_url,
                            truncate=not changelog)
    if changelog:
        def save(receipt):
            receipt.update({'tag': tag, 'workflow_url': workflow_url,
                            'release_url': payload['embeds'][0]['url']})
            receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')

        publish([payload], 'slskR', tag, project, changelog, on_progress=save)
        return

    print('::warning::DISCORD_CHANGELOG_WEBHOOK is unset; using the existing project channel.')
    receipt = execute_webhook(project, payload)
    receipt.update({'tag': tag, 'workflow_url': workflow_url})
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f"Discord confirmed message {receipt['message_id']} for {tag}.")
    with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a') as summary:
        summary.write(f"Announced [{tag}]({receipt['release_url']}) on Discord. "
                      f"Message ID: `{receipt['message_id']}`; channel ID: `{receipt['channel_id']}`.\n")


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError) as error:
        sys.exit(str(error))
