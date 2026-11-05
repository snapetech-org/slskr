#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import subprocess

R = Path(__file__).resolve().parent
REPO = Path(subprocess.check_output(['git', '-C', str(R), 'rev-parse', '--show-toplevel'], text=True).strip())
HEAD = 'e1ccc3d6509baf957f3039046e5b66dda3ae15d0'
TREE = 'd7c7aa967cb7faf51a8211a397859feebe8129b8'
PRODUCT = 'dab83932bb2b375caf3f588ac7b20b3bd835a419'

def sha(x):
    return hashlib.sha256(x.encode('utf-8') if isinstance(x, str) else x).hexdigest()

def j(path):
    return json.loads(path.read_text(encoding='utf-8'))

def jl(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()

def git_bytes(ref, path):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', f'{ref}:{path}'])

def verify_packet(folder):
    sums = {}
    for line in (folder / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.lstrip('* ')
        assert name not in sums
        sums[name] = digest
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p != folder / 'SHA256SUMS.txt'}
    assert actual == set(sums), (folder, actual ^ set(sums))
    for name, digest in sums.items():
        assert sha((folder / name).read_bytes()) == digest, name
    return sums

def main():
    outer = verify_packet(R)
    app_manifest = j(R / 'application-manifest.json')
    actual = {p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and p not in {R / 'SHA256SUMS.txt', R / 'application-manifest.json'}}
    assert set(app_manifest['fileHashes']) == actual
    for name, pin in app_manifest['fileHashes'].items():
        raw = (R / name).read_bytes()
        assert sha(raw) == pin['sha256'] and len(raw) == pin['byteCount']

    cf = R / 'review-inputs' / 'candidate-free-input'
    primary = R / 'review-inputs' / 'primary-review'
    blind = R / 'review-inputs' / 'independent-blind-review'
    root = R / 'review-inputs' / 'root-manual-review'
    cross_dir = R / 'cross-review'
    packets = [verify_packet(x) for x in [cf, primary, blind, root, cross_dir]]
    im = j(cf / 'manifest.json')
    ps = j(primary / 'SUMMARY.json')
    bp = j(blind / 'review-packet.json')
    xp = j(cross_dir / 'cross-review.json')
    assert (im['head'], im['tree']) == (HEAD, TREE)
    assert (ps['head'], ps['tree']) == (HEAD, TREE)
    assert (bp['binding']['head'], bp['binding']['tree']) == (HEAD, TREE)
    assert (xp['binding']['head'], xp['binding']['tree']) == (HEAD, TREE)
    assert im['carryForwardHoldCount'] == im['carryForwardHoldUnchangedCount'] == 62
    assert xp['summary']['acceptCurrent'] == 236 and xp['summary']['proposeCorrection'] == 2
    assert xp['summary']['proposeRefinement'] == 2 and xp['summary']['textFreeHold'] == 0

    cells = jl(cf / 'current-target-cells.jsonl')
    cross_rows = xp['cells']
    readback = jl(R / 'apply-readback-cells.jsonl')
    selected = j(R / 'exact-hash-apply-plan.json')
    cell_by = {(x['position'], x['locale']): x for x in cells}
    cross_by = {(x['position'], x['locale']): x for x in cross_rows}
    read_by = {(x['position'], x['locale']): x for x in readback}
    selected_by = {(x['position'], x['locale']): x for x in selected['selectedChanges']}
    accepted_by = {(x['position'], x['locale']): x for x in selected['acceptedHashOnly']}
    root_rows = {(x['position'], x['locale']): x for x in jl(root / 'approved-targets.jsonl')}
    assert len(cell_by) == len(cross_by) == len(read_by) == 240
    assert len(selected_by) == len(root_rows) == 4 and len(accepted_by) == 236
    assert selected_by.keys() == root_rows.keys()
    assert set(selected_by) | set(accepted_by) == set(cell_by)

    assert selected['inputHead'] == HEAD and selected['inputTree'] == TREE
    assert selected['productCommit'] == PRODUCT and selected['productCommitParent'] == HEAD
    assert git('rev-parse', PRODUCT + '^') == HEAD
    assert git('rev-parse', PRODUCT + '^{tree}') == selected['productTree']
    product_paths = set(git('diff-tree', '--no-commit-id', '--name-only', '-r', PRODUCT).splitlines())
    expected_paths = {
        'web/src/lib/locales/ui-labels.pt-BR.json',
        'web/src/lib/locales/ui-labels.vi.json',
        'web/src/lib/locales/ui-labels.zh-Hant.json',
    }
    assert product_paths == expected_paths
    assert not any(x.startswith('.github/workflows/') for x in product_paths)

    catalog_meta = j(cf / 'catalog-file-pins.json')['localeCatalogs']
    before = {}
    after = {}
    for locale, pin in catalog_meta.items():
        path = pin['path']
        before_bytes = git_bytes(HEAD, path)
        after_bytes = git_bytes(PRODUCT, path)
        old = json.loads(before_bytes.decode('utf-8'))
        new = json.loads(after_bytes.decode('utf-8'))
        pre_pin = selected['preApplyCatalogPins'][path]
        post_pin = selected['postimageCatalogPins'][path]
        assert len(old) == len(new) == pin['keyCount'] == pre_pin['keyCount'] == post_pin['keyCount'] == 5441
        assert list(old) == list(new)
        order_sha = sha('\n'.join(old) + '\n')
        assert order_sha == pin['orderedKeySha256'] == pre_pin['orderedKeySha256'] == post_pin['orderedKeySha256']
        assert sha(before_bytes) == pin['sha256'] == pre_pin['sha256']
        assert git('rev-parse', f'{HEAD}:{path}') == pin['gitBlob'] == pre_pin['gitBlob']
        assert sha(after_bytes) == post_pin['sha256'] and len(after_bytes) == post_pin['byteCount']
        assert git('rev-parse', f'{PRODUCT}:{path}') == post_pin['gitBlob']
        before[locale], after[locale] = old, new
    changed_by_locale = {
        locale: {key for key in before[locale] if before[locale][key] != after[locale][key]}
        for locale in catalog_meta
    }
    expected_by_locale = {
        locale: {cell_by_key['sourceKey'] for pair, cell_by_key in cell_by.items()
                 if pair in selected_by and pair[1] == locale}
        for locale in catalog_meta
    }
    assert changed_by_locale == expected_by_locale

    for cell in cells:
        pair = (cell['position'], cell['locale'])
        cross = cross_by[pair]
        rb = read_by[pair]
        old = before[cell['locale']][cell['sourceKey']]
        new = after[cell['locale']][cell['sourceKey']]
        assert old == cell['currentTarget'] and sha(old) == cell['currentTargetSha256']
        assert rb['readbackMatches'] is True and rb['observedAfterTarget'] == new
        if pair in selected_by:
            pick = selected_by[pair]
            assert new == pick['selectedTarget'] and sha(new) == pick['selectedTargetSha256']
            assert root_rows[pair]['selectedTarget'] == new
            assert cross['crossTarget'] == new
        else:
            assert new == old and cross['crossDisposition'] == 'accept-current'
            assert pair in accepted_by

    prior_holds = jl(cf / 'prior-hold-hash-reattestation.jsonl')
    queue = {x['position']: x['sourceKey'] for x in jl(cf / 'source-queue.jsonl')}
    assert len(prior_holds) == 62
    for hold in prior_holds:
        source = queue[hold['position']]
        path = catalog_meta[hold['locale']]['path']
        old = json.loads(git_bytes(HEAD, path).decode('utf-8'))[source]
        new = json.loads(git_bytes(PRODUCT, path).decode('utf-8'))[source]
        assert sha(old) == hold['priorTargetSha256'] == sha(new)

    old_body = (R / 'pr-before-body.md').read_text(encoding='utf-8')
    new_body = (R / 'pr-after-body.md').read_text(encoding='utf-8')
    assert old_body == j(R / 'pr-before.json')['body']
    assert new_body == j(R / 'pr-after.json')['body'] and new_body.startswith(old_body)
    assert j(R / 'pr-after.json')['head']['sha'] == PRODUCT
    print(json.dumps({'result':'PASS','productCommit':PRODUCT,'selectedChanges':4,'acceptedHashOnly':236,
                      'priorHoldsReattested':62,'browserReviewPerformed':False,'nativeSpeakerSignoff':False},indent=2))

if __name__ == '__main__':
    main()
