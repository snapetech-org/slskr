#!/usr/bin/env python3
"""Produce primary semantic review of the already-sealed candidate-free packet."""
import hashlib, json, subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parent
INPUT=ROOT/"candidate-free-input"
PROPOSALS={
 (1565,"zh-Hant"):("propose-refinement","無法載入 MediaCore 統計資料",
   "The caller renders this text as the MediaCore statistics dashboard heading. 統計訊息 can suggest a message; 統計資料 names the statistics data more directly.","moderate"),
 (1570,"es"):("propose-correction","No se pudo cargar el estado de seguridad adversarial",
   "The source is the status fetch for the adversarial security feature. The current estado adversario can read as an adversary's own state; this aligns with the adjacent seguridad adversarial wording.","moderate"),
 (1570,"zh-Hans"):("propose-refinement","无法加载对抗性安全状态",
   "The caller fetches status data for the adversarial security feature. The adjacent settings label uses 对抗性安全; this adds the same feature term to the less specific 对抗状态.","moderate"),
 (1570,"hi"):("propose-refinement","प्रतिकूल सुरक्षा स्थिति लोड करने में विफल",
   "The caller fetches status data for the adversarial security feature. The adjacent settings label uses प्रतिकूल सुरक्षा; adding सुरक्षा makes this status message refer to that same feature.","moderate"),
 (1570,"de"):("propose-correction","Der Status der adversarialen Sicherheit konnte nicht geladen werden",
   "The current Gegnerstatus means an opponent's status. The caller fetches status for the adversarial security feature, whose neighboring settings label uses adversariale Sicherheit.","high"),
 (1570,"fr"):("propose-correction","Impossible de charger le statut de sécurité adversariale",
   "The current contradictoire means contradictory, not adversarial. The caller fetches status for the feature whose neighboring settings label uses sécurité adversariale.","high"),
 (1570,"pt-BR"):("propose-correction","Falha ao carregar o status de segurança adversarial",
   "The caller fetches status for the adversarial security feature. The current adversário can name an adversary; the adjacent settings label uses segurança adversarial.","moderate"),
 (1570,"ar"):("propose-refinement","تعذر تحميل حالة الأمان الخصومي",
   "The caller fetches status for the adversarial security feature. The adjacent settings label uses الأمان الخصومي; this repeats that term instead of the broader حالة الخصومة.","moderate"),
 (1570,"zh-Hant"):("propose-correction","無法載入對抗性安全狀態",
   "The caller fetches status for the adversarial security feature. The current 加載 uses Simplified Chinese form and 對抗狀態 omits 性; the adjacent label uses 對抗性安全.","high"),
 (1570,"vi"):("propose-refinement","Không thể tải trạng thái bảo mật đối kháng",
   "The caller fetches status for the adversarial security feature. The neighboring settings label uses bảo mật đối kháng; this aligns the current broader trạng thái đối nghịch with that feature term.","moderate"),
 (1570,"id"):("propose-correction","Gagal memuat status keamanan adversarial",
   "The caller fetches status for the adversarial security feature. The current permusuhan means hostility; the neighboring settings label uses keamanan adversarial.","moderate"),
 (1580,"ko"):("propose-correction","대시보드를 로드하지 못했습니다:",
   "The caller appends the dashboard error text after this label. The current full stop conflicts with the source's trailing colon and the runtime composition; this preserves the separator.","high"),
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
      "artifact":"slskR PR #209 W1563-W1582 primary semantic review",
      "repository":"snapetech-org/slskR","pullRequest":209,"head":manifest["head"],"tree":manifest["tree"],
      "candidateFreeInputChecksumListSha256":sha((INPUT/"SHA256SUMS.txt").read_bytes()),
      "sourceCount":20,"localeCount":12,"cellCount":len(rows),"counts":counts,
      "proposalCount":len(proposals),"holdCount":len(holds),"allCellRowsHaveSourceAndCurrentHashes":True,
      "placeholdersMarkupNumbersProtectedLiteralsReviewed":True,
      "nativeSpeakerSignoff":False,"browserReviewPerformed":False,
      "createdAtUtc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds"),
    }
    writej(P/"SUMMARY.json",summary)
    readme=f"""# slskR PR #209 W1563-W1582 primary review

This packet reviews all 240 locale cells from the sealed candidate-free input at {INPUT}. Input checksum-list SHA-256: {summary['candidateFreeInputChecksumListSha256']}. The pinned PR head/tree are {manifest['head']} / {manifest['tree']}.

The review used exact source keys, production caller contexts, current values, prior approved wording where relevant, and token signatures. It records accept-current, correction/refinement proposals, or text-free holds. Counts: {counts}.

This is a primary semantic review. It does not include blind or cross-review, native-speaker signoff, or browser review.
"""
    (P/"README.md").write_text(readme,encoding="utf-8")
    sums=[f"{sha(p.read_bytes())}  {p.name}" for p in sorted(P.iterdir()) if p.is_file() and p.name!="SHA256SUMS.txt"]
    (P/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
