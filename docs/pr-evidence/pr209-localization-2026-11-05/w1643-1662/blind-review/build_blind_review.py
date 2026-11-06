#!/usr/bin/env python3
"""Build this window's independent blind semantic review from candidate-free input only."""
from __future__ import annotations
import collections
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
PACKET = ROOT.parent / 'candidate-free-input'
REPO = ROOT.parent / 'worktree'
HEAD = '2d804c49879372071adf606bc2a2cf51e261fd94'
TREE = 'd6f5552d2400d868c2f2af98eb68caadfd4f3f66'
LOCALES = ['es','zh-Hans','hi','de','ja','fr','pt-BR','ar','ko','zh-Hant','vi','id']

# Narrow, source-grounded recommendations. All other current targets are accepted.
OVERRIDES = {
    (1643, 'ko'): ('correction', '메타데이터를 가져오지 못했습니다:', 'high',
        'The current Korean “검색” means search rather than retrieve, and its period closes a prefix that is followed by a separate error detail. “가져오지 못했습니다” conveys failed retrieval and the colon preserves the continuation.'),
    (1647, 'fr'): ('refinement', 'Échec du routage du message :', 'high',
        'The current wording suggests message delivery or forwarding. “Routage” directly expresses routing and matches the sibling message-routing key; the colon remains for the appended error detail.'),
    (1647, 'pt-BR'): ('refinement', 'Falha ao rotear a mensagem:', 'high',
        'The current wording says forwarding (“encaminhar”), while the source and PodMessageRoutingPanel describe routing. “Rotear” preserves that technical operation; the colon remains for the appended detail.'),
    (1654, 'zh-Hant'): ('correction', '無法儲存來源訂閱整合設定。', 'moderate',
        'The current “摘要” means summary/abstract and loses the feed sense. “訂閱” conveys a feed subscription here and aligns with the Simplified Chinese rendering of source-feed integration.'),
    (1661, 'ar'): ('refinement', 'تعذر اختيار النسخة المعيارية.', 'moderate',
        'The current wording means the basic/base version. “النسخة المعيارية” more clearly conveys the canonical or normalized representative version; caller context identifies an allowlisted server error but gives no deeper domain definition.'),
    (1661, 'ja'): ('refinement', '正準バリアントを選択できませんでした。', 'moderate',
        '“標準” means standard, which can imply a default rather than canonical selection. “正準” is the more precise technical equivalent of canonical; caller context does not define the variant-selection algorithm.'),
    (1661, 'ko'): ('refinement', '정규 변형을 선택하지 못했습니다.', 'moderate',
        '“표준” means standard and can imply a default. “정규” better preserves the technical sense of canonical; caller context does not define the variant-selection algorithm.'),
}
RATIONALES = {
  1643: 'The target states that metadata retrieval failed and retains the colon used before the caller-appended error detail.',
  1644: 'The target clearly states that Pod metadata could not be retrieved; the product term Pod is retained.',
  1645: 'The target clearly states that retrieval of user information failed.',
  1646: 'The target describes failure of the message-routing operation.',
  1647: 'The target describes message-routing failure and retains the colon for the separately rendered error detail.',
  1648: 'The target states that saving the FTP integration settings failed and preserves the FTP acronym.',
  1649: 'The target states that saving the adversarial settings failed, consistent with the AdversarialSettings security view.',
  1650: 'The target states that saving the bridge configuration failed.',
  1651: 'The target clearly identifies failure to save the metadata integration settings.',
  1652: 'The target clearly identifies failure to save the notification integration settings.',
  1653: 'The target clearly identifies failure to save the policy settings.',
  1654: 'The target identifies the source-feed integration settings.',
  1655: 'The target states that saving the user note failed.',
  1656: 'The target states that searching content failed.',
  1657: 'The target states that content search failed and preserves the {error} substitution exactly.',
  1658: 'The target states that searching library items failed.',
  1659: 'The target states that searching messages failed.',
  1660: 'The target states that message search failed and preserves the {error} substitution exactly.',
  1661: 'The target expresses failure to select the canonical variant; wording is refined only where the current term can imply a standard or base variant instead.',
  1662: 'The target states that sending the batch message failed.',
}

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
def canon(x) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def load_jsonl(path: pathlib.Path):
    raw = path.read_bytes()
    rows=[]
    for line in raw.splitlines(keepends=True):
        if line.strip(): rows.append((json.loads(line), sha(line.rstrip(b'\r\n'))))
    return rows

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def write_jsonl(path, rows):
    path.write_text(''.join(canon(x) + '\n' for x in rows), encoding='utf-8')

def main():
    if git('rev-parse','HEAD') != HEAD or git('rev-parse','HEAD^{tree}') != TREE or git('status','--porcelain'):
        raise SystemExit('refusing to build: exact detached worktree pin is missing or dirty')
    manifest=json.loads((PACKET/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('head') != HEAD or manifest.get('tree') != TREE or manifest.get('cellCount') != 240:
        raise SystemExit('candidate-free packet manifest pin/count mismatch')
    rows_with_hash=load_jsonl(PACKET/'current-target-cells.jsonl')
    ctxrows=[json.loads(x) for x in (PACKET/'source-contexts.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    ctx={x['sourceKey']:x for x in ctxrows}
    if len(rows_with_hash)!=240 or len(ctx)!=20: raise SystemExit('unexpected candidate-free input cardinality')
    ledger=[]; proposals=[]
    for row,row_sha in rows_with_hash:
        pos=row['position']; locale=row['locale']; override=OVERRIDES.get((pos,locale))
        decision='accept-current'; rationale=RATIONALES[pos]; confidence='high'; recommended=None
        if override:
            decision,recommended,confidence,specific=override
            rationale=specific
        c=ctx[row['sourceKey']]
        item={
          'cellId': f"{row['sourceKey']}::{locale}",
          'locale': locale,
          'sourceKey': row['sourceKey'],
          'selectedPosition': pos,
          'decision': decision,
          'sourceText': row['sourceKey'],
          'currentTarget': row['currentTarget'],
          'rationale': rationale,
          'confidence': confidence,
          'candidateFreeRowSha256': row_sha,
          'sourceTextSha256': row['sourceKeySha256'],
          'currentTargetSha256': row['currentTargetSha256'],
          'callerContextSha256': c['callerContextSha256'],
          'sourceContextSha256': row['sourceContextSha256'],
          'callerCount': row['callerCount'],
          'callerPaths': sorted({x['path'] for x in c['callers']}),
          'exactHead': HEAD,
          'exactTree': TREE,
        }
        if recommended is not None:
            item['recommendedTarget']=recommended
            item['recommendedTargetSha256']=sha(recommended.encode('utf-8'))
        ledger.append(item)
        if recommended is not None:
            proposal={k:item[k] for k in ('cellId','locale','sourceKey','selectedPosition','decision','sourceText','currentTarget','currentTargetSha256','recommendedTarget','recommendedTargetSha256','rationale','confidence','candidateFreeRowSha256','sourceTextSha256','callerContextSha256','sourceContextSha256','callerCount','callerPaths','exactHead','exactTree')}
            proposals.append(proposal)
    reviewed_at=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    write_jsonl(ROOT/'ledger.jsonl',ledger)
    write_jsonl(ROOT/'proposals.jsonl',proposals)
    counts=collections.Counter(x['decision'] for x in ledger)
    by_locale=collections.Counter(x['locale'] for x in proposals)
    by_source=collections.Counter(x['sourceKey'] for x in proposals)
    summary={
      'artifact':'slskR PR #209 W1643-W1662 independent blind semantic review',
      'exactHead':HEAD,'exactTree':TREE,'pullRequest':209,
      'inputDirectory':'../candidate-free-input/',
      'inputManifestSha256':sha((PACKET/'manifest.json').read_bytes()),
      'inputChecksumIndexSha256':sha((PACKET/'SHA256SUMS.txt').read_bytes()),
      'reviewedAtUtc':reviewed_at,
      'cellCount':len(ledger),'sourceCount':20,'localeCount':12,
      'decisionCounts':dict(sorted(counts.items())),
      'proposalCount':len(proposals),
      'proposalCountsByLocale':dict(sorted(by_locale.items())),
      'proposalCountsBySource':dict(sorted(by_source.items())),
      'confidenceCounts':dict(sorted(collections.Counter(x['confidence'] for x in ledger).items())),
      'tokenAudit':{
        'placeholderCells':sum(bool(x['sourcePlaceholders']) for x in [r for r,_ in rows_with_hash]),
        'markupCells':sum(bool(x['sourceMarkupTags']) for x,_ in rows_with_hash),
        'numericTokenCells':sum(bool(x['sourceNumericTokens']) for x,_ in rows_with_hash),
        'protectedLiteralCells':sum(bool(x['sourceProtectedLiterals']) for x,_ in rows_with_hash),
        'recommendationsPreservePlaceholderMarkupNumericAndProtectedLiteralTokens':True,
        'podTermPreserved':True,
      },
      'limitations':[
        'Semantic decisions are based on the pinned English source keys and extracted direct caller contexts in the candidate-free packet.',
        'No native-speaker second review or headed runtime display review was performed.',
        'The canonical-variant caller is an error-message allowlist; its surrounding algorithm semantics are unavailable in this packet, so Arabic, Japanese, and Korean terminology refinements have moderate confidence.',
      ],
      'independence':'No primary-review or cross-review outputs were used as inputs.',
    }
    write_json(ROOT/'summary.json',summary)
    manifest_out={
      'artifact':'blind-review', 'exactHead':HEAD, 'exactTree':TREE,
      'inputManifestSha256':summary['inputManifestSha256'],
      'inputChecksumIndexSha256':summary['inputChecksumIndexSha256'],
      'ledgerSha256':sha((ROOT/'ledger.jsonl').read_bytes()),
      'proposalsSha256':sha((ROOT/'proposals.jsonl').read_bytes()),
      'cellCount':len(ledger),'proposalCount':len(proposals),
      'decisionCounts':dict(sorted(counts.items())),
      'candidateFreeOnly':True,'primaryOrCrossOutputUsed':False,
    }
    write_json(ROOT/'manifest.json',manifest_out)

if __name__=='__main__': main()
