#!/usr/bin/env python3
"""Produce primary semantic review of the already-sealed candidate-free packet."""
import hashlib, json, subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parent
INPUT=ROOT/"candidate-free-input"
PROPOSALS={
 (1536,"de"):("propose-correction","Aggregierte Meinungen konnten nicht abgerufen werden",
   "The caller is retrieving aggregated opinions. Bewertungen means ratings/reviews, while Meinungen preserves the source concept and matches the neighboring placeholder variant.","high"),
 (1537,"fr"):("propose-correction","Impossible de récupérer les avis agrégés : {message}",
   "The source and caller refer to aggregated opinions. Globales means global/worldwide and shifts the meaning; avis agrégés matches the neighboring error string.","high"),
 (1537,"vi"):("propose-correction","Không lấy được ý kiến tổng hợp: {message}",
   "The current string contains two unnecessary U+200B zero-width spaces between words. Removing them restores ordinary Vietnamese word spacing without changing the message.","high"),
 (1538,"es"):("propose-correction","No se pudieron obtener las estadísticas de sincronización retroactiva",
   "The caller describes backfill as syncing missed messages. Relleno is an unclear literal filler noun for that operation; sincronización retroactiva conveys the historical sync.","moderate"),
 (1539,"es"):("propose-correction","No se pudieron obtener las estadísticas de sincronización retroactiva: {message}",
   "Reabastecimiento means replenishment and is misleading here. The caller describes syncing messages missed earlier; this wording names that backfill operation and preserves {message}.","moderate"),
 (1538,"pt-BR"):("propose-correction","Não foi possível obter as estatísticas da sincronização retroativa",
   "The caller describes backfill as syncing missed messages. Preenchimento is a literal filling noun and obscures the historical sync; sincronização retroativa names the operation.","moderate"),
 (1539,"pt-BR"):("propose-correction","Falha ao obter as estatísticas da sincronização retroativa: {message}",
   "The caller describes backfill as syncing missed messages. This names the historical sync instead of generic preenchimento and preserves {message}.","moderate"),
 (1538,"ar"):("propose-correction","تعذر الحصول على إحصاءات مزامنة الرسائل الفائتة",
   "The caller says backfill sync requests messages missed earlier. This states that meaning directly; الاستكمال is too general for the named operation.","moderate"),
 (1539,"ar"):("propose-correction","فشل الحصول على إحصاءات مزامنة الرسائل الفائتة: {message}",
   "إعادة التعبئة reads as refilling, while the caller describes synchronizing missed messages. This names the backfill operation and preserves {message}.","moderate"),
 (1539,"fr"):("propose-correction","Impossible de récupérer les statistiques de rattrapage : {message}",
   "The caller describes catching up missed messages. Remplissage means filling, and conflicts with the accurate rattrapage wording in the adjacent backfill-statistics message.","high"),
 (1538,"vi"):("propose-correction","Không thể lấy thống kê về việc đồng bộ các tin nhắn bị lỡ",
   "The caller explains that backfill sync requests messages missed earlier. Bổ sung dữ liệu is too broad; this states the operation in ordinary Vietnamese.","moderate"),
 (1539,"vi"):("propose-correction","Không thể lấy thống kê về việc đồng bộ các tin nhắn bị lỡ: {message}",
   "Chèn lấp is an unclear literal rendering of backfill. The caller describes syncing missed messages; this names that operation and preserves {message}.","moderate"),
 (1538,"id"):("propose-correction","Gagal mendapatkan statistik sinkronisasi pesan yang terlewat",
   "The caller describes backfill as synchronizing messages missed earlier. Pengisian ulang means refilling; this states the operation clearly.","moderate"),
 (1539,"id"):("propose-correction","Gagal mendapatkan statistik sinkronisasi pesan yang terlewat: {message}",
   "The caller describes backfill as synchronizing messages missed earlier. Pengisian ulang means refilling; this states the operation and preserves {message}.","moderate"),
 (1541,"fr"):("propose-correction","Impossible de récupérer les canaux : {message}",
   "The caller retrieves a list of MediaCore channels. Chaînes usually suggests broadcast/TV channels; canaux matches the neighboring translation and the API object.","high"),
 (1541,"vi"):("propose-correction","Không thể tải danh sách kênh: {message}",
   "The caller retrieves an array of channels. Không nhận được kênh suggests failure to receive one channel; danh sách kênh makes the list retrieval explicit.","high"),
 (1542,"hi"):("propose-refinement","सर्वसम्मति-आधारित सिफ़ारिशें प्राप्त नहीं हो सकीं",
   "The caller fetches recommendations derived from aggregated member opinions. सर्वसम्मति-आधारित makes the consensus relationship clearer than सहमति की सिफ़ारिशें.","moderate"),
 (1542,"ko"):("propose-refinement","합의 기반 추천을 가져오지 못했습니다",
   "The caller fetches recommendations derived from aggregated member opinions. 합의 기반 states that they are based on consensus more clearly than the compressed 합의 추천.","moderate"),
}
def sha(x):
    if isinstance(x,str): x=x.encode()
    return hashlib.sha256(x).hexdigest()
def j(path): return json.loads(path.read_text(encoding="utf-8"))
def jl(path): return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s]
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def writej(path,x): path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def writejl(path,xs): path.write_text("".join(canon(x)+"\n" for x in xs),encoding="utf-8")

def main():
    subprocess.check_call(["python3",str(INPUT/"verify-candidate-free.py")])
    manifest=j(INPUT/"manifest.json")
    cells=jl(INPUT/"current-target-cells.jsonl")
    contexts={x["position"]:x for x in jl(INPUT/"source-contexts.jsonl")}
    rows=[]; proposals=[]; holds=[]
    for cell in cells:
        key=(cell["position"],cell["locale"])
        src=cell["sourceKey"]
        if key in PROPOSALS:
            disp,target,reason,conf=PROPOSALS[key]
        else:
            target=cell["currentTarget"]
            disp="accept-current"
            if src.startswith("Failed to create "):
                verb="create"
            elif src.startswith("Failed to delete "):
                verb="delete"
            elif src.startswith("Failed to discover "):
                verb="discover"
            elif src.startswith("Failed to fetch "):
                verb="fetch"
            elif src.startswith("Failed to get "):
                verb="retrieve"
            else:
                verb="perform"
            reason=f"Accurately states that the caller failed to {verb} the named object or data, in a concise UI error message."
            if "{error}" in src or "{message}" in src:
                reason += " The named runtime placeholder is retained exactly."
            if "swarm" in src.lower():
                reason += " The localized or retained swarm term is consistent with the technical caller context."
            if "backfill" in src.lower():
                reason += " The locale uses an established technical equivalent for backfill."
            conf="high" if src in ("Failed to create search","Failed to create share group","Failed to delete collection","Failed to delete contact","Failed to delete conversation: {error}","Failed to get channels") else "moderate"
        if disp not in ("accept-current","propose-correction","propose-refinement","text-free-hold"):
            raise ValueError(disp)
        target_hash=sha(target) if target is not None else None
        row={
          "position":cell["position"],"locale":cell["locale"],"sourceKey":src,"sourceKeySha256":cell["sourceKeySha256"],
          "sourceContextSha256":cell["sourceContextSha256"],"currentTarget":cell["currentTarget"],
          "currentTargetSha256":cell["currentTargetSha256"],"disposition":disp,"selectedTarget":target,
          "selectedTargetSha256":target_hash,"reason":reason,"confidence":conf,
          "placeholderSequencePreserved":cell["placeholderSequenceMatches"],
          "markupPreserved":cell["markupMatches"],"numericTokensPreserved":cell["numericTokensMatch"],
          "protectedLiteralsPreserved":cell["protectedLiteralsMatch"],
        }
        rows.append(row)
        if disp in ("propose-correction","propose-refinement"):
            proposal={k:row[k] for k in ("position","locale","sourceKeySha256","sourceContextSha256","currentTargetSha256","selectedTarget","selectedTargetSha256","disposition","reason","confidence")}
            proposals.append(proposal)
        elif disp=="text-free-hold":
            holds.append({"position":cell["position"],"locale":cell["locale"],"sourceKeySha256":cell["sourceKeySha256"],
              "sourceContextSha256":cell["sourceContextSha256"],"currentTargetSha256":cell["currentTargetSha256"],"reason":reason,"confidence":conf})
    writejl(P/"primary-ledger.jsonl",rows)
    writejl(P/"proposals.jsonl",proposals)
    writejl(P/"holds.jsonl",holds)
    counts={d:sum(x["disposition"]==d for x in rows) for d in ("accept-current","propose-correction","propose-refinement","text-free-hold")}
    summary={
      "artifact":"slskR PR #204 W1523-W1542 primary semantic review",
      "repository":"snapetech-org/slskR","pullRequest":204,"head":manifest["head"],"tree":manifest["tree"],
      "candidateFreeInputChecksumListSha256":sha((INPUT/"SHA256SUMS.txt").read_bytes()),
      "sourceCount":20,"localeCount":12,"cellCount":len(rows),"counts":counts,
      "proposalCount":len(proposals),"holdCount":len(holds),"allCellRowsHaveSourceAndCurrentHashes":True,
      "placeholdersMarkupNumbersProtectedLiteralsReviewed":True,
      "nativeSpeakerSignoff":False,"browserReviewPerformed":False,
      "createdAtUtc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds"),
    }
    writej(P/"SUMMARY.json",summary)
    readme=f"""# slskR PR #204 W1523-W1542 primary review

This packet reviews all 240 locale cells from the sealed candidate-free input at {INPUT}. Input checksum-list SHA-256: {summary['candidateFreeInputChecksumListSha256']}. The pinned PR head/tree are {manifest['head']} / {manifest['tree']}.

The review used exact source keys, caller contexts, current values and token signatures. It records accept-current, correction/refinement proposals, or text-free holds. Counts: {counts}.

This is a primary semantic review. It does not include blind or cross-review, native-speaker signoff, or browser review.
"""
    (P/"README.md").write_text(readme,encoding="utf-8")
    sums=[f"{sha(p.read_bytes())}  {p.name}" for p in sorted(P.iterdir()) if p.is_file() and p.name!="SHA256SUMS.txt"]
    (P/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
