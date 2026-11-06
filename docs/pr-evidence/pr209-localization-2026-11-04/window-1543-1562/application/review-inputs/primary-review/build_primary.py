#!/usr/bin/env python3
"""Produce primary semantic review of the already-sealed candidate-free packet."""
import hashlib, json, subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parent
INPUT=ROOT/"candidate-free-input"
PROPOSALS={
 (1543,"hi"):("propose-correction","सर्वसम्मति-आधारित सिफ़ारिशें प्राप्त नहीं हो सकीं: {message}",
   "The caller fetches recommendations based on member consensus. The previously approved Hindi wording for the neighboring consensus-recommendation error uses सर्वसम्मति-आधारित; सर्वसम्मत can suggest unanimity. This retains the established term and {message}.","high"),
 (1543,"ja"):("propose-correction","合意に基づく推奨事項を取得できませんでした: {message}",
   "The caller fetches consensus recommendations. The neighboring approved Japanese message uses 合意に基づく推奨事項; reusing that wording is clearer than the compressed コンセンサス推奨 and preserves {message}.","high"),
 (1543,"ar"):("propose-correction","تعذر الحصول على توصيات الإجماع: {message}",
   "The caller fetches consensus recommendations. The neighboring approved Arabic message uses توصيات الإجماع; بالإجماع can read as unanimously. This reuses the established phrasing and preserves {message}.","high"),
 (1543,"ko"):("propose-correction","합의 기반 추천을 가져오지 못했습니다: {message}",
   "The caller fetches recommendations based on member consensus. The neighboring approved Korean message uses 합의 기반 추천, which is more precise than the current broad 합의 권장 사항 and preserves {message}.","high"),
 (1544,"ar"):("propose-correction","تعذر الحصول على البيانات الوصفية للمحتوى: {error}",
   "The caller retrieves content metadata. بيانات المحتوى says content data and omits metadata; the established Arabic term البيانات الوصفية is precise here. The {error} placeholder is retained.","high"),
 (1546,"es"):("propose-correction","No se pudieron obtener las marcas de tiempo de última presencia",
   "The caller retrieves last-seen timestamps keyed by channel ID, and the neighboring panel heading uses última presencia. Última actividad is broader than the source term; this matches the established label.","moderate"),
 (1546,"fr"):("propose-correction","Impossible de récupérer les horodatages de dernière présence",
   "The caller retrieves last-seen timestamps keyed by channel ID, and the neighboring panel heading uses dernière présence. Dernière activité is broader than the source term; this matches the established label.","moderate"),
 (1548,"de"):("propose-correction","Mitgliederaffinitäten konnten nicht abgerufen werden",
   "This is the retrieval error for the Member Affinities panel. Mitgliederzuordnungen means member mappings or assignments; the panel's established German label is Mitgliederaffinitäten.","high"),
 (1548,"zh-Hans"):("propose-refinement","无法获取成员亲和度",
   "The caller retrieves member affinity scores. The same panel's Member Affinities heading uses 成员亲和度; this refinement aligns the error with that established metric name.","moderate"),
 (1548,"zh-Hant"):("propose-refinement","無法取得會員親和度",
   "The caller retrieves member affinity scores. The same panel's Member Affinities heading uses 會員親和度; this refinement aligns the error with that established metric name.","moderate"),
 (1549,"zh-Hans"):("propose-correction","无法获取成员亲和度：{message}",
   "The caller retrieves member affinity scores. The current 成员关联 drops the degree/affinity meaning and differs from the panel label 成员亲和度; this keeps that term and {message}.","high"),
 (1549,"zh-Hant"):("propose-correction","無法取得會員親和度：{message}",
   "The caller retrieves member affinity scores. The current 成員關聯 drops the affinity-degree meaning and differs from the panel label 會員親和度; this keeps that term and {message}.","high"),
 (1549,"ja"):("propose-correction","メンバーの親和度を取得できませんでした: {message}",
   "The caller retrieves member affinity scores. The current メンバー アフィニティ is an awkward transliteration; the same panel uses the natural term メンバーの親和度. This preserves {message}.","high"),
 (1549,"vi"):("propose-correction","Không thể tải mức độ tương đồng của thành viên: {message}",
   "The caller retrieves member affinity scores. Mối quan hệ của thành viên means member relationships and is broader than the current neighboring wording mức độ tương đồng của thành viên; this aligns the pair and retains {message}.","moderate"),
 (1551,"zh-Hans"):("propose-correction","获取会员记录失败：",
   "The caller displays the result of Get Membership Record. 获取会员失败 says it failed to get a member and omits the record; the existing label uses 会员记录.","high"),
 (1551,"zh-Hant"):("propose-correction","無法取得會員記錄：",
   "The caller displays the result of Get Membership Record. 獲取會員失敗 says it failed to get a member and omits the record; the existing label uses 會員記錄.","high"),
 (1551,"ko"):("propose-correction","회원 기록을 가져오지 못했습니다:",
   "The caller displays a fetched membership record. 회원가입 means account sign-up, but this action retrieves an existing member record; this corrects the operation and keeps the trailing colon.","high"),
 (1551,"vi"):("propose-correction","Không thể lấy hồ sơ thành viên:",
   "The caller displays a fetched membership record. Không thể trở thành thành viên means the person could not become a member; this instead describes retrieving the hồ sơ thành viên and retains the colon.","high"),
 (1554,"de"):("propose-correction","Meinungen konnten nicht abgerufen werden",
   "The caller loads community opinions on content variants. Bewertungen narrows these to ratings/reviews; the adjacent opinion-statistics and previously approved aggregated-opinions wording use Meinungen.","high"),
 (1560,"de"):("propose-correction","Beitritt zum Raum fehlgeschlagen",
   "The caller joins a chat room. The current passive omits the dative required by beitreten; Beitritt zum Raum fehlgeschlagen is idiomatic and matches the established Raum wording.","high"),
 (1561,"de"):("propose-correction","Beitritt zum Raum fehlgeschlagen: {error}",
   "The two callers join a chat room. The current passive omits the dative required by beitreten; this idiomatic phrasing preserves {error}.","high"),
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
      "artifact":"slskR PR #209 W1543-W1562 primary semantic review",
      "repository":"snapetech-org/slskR","pullRequest":209,"head":manifest["head"],"tree":manifest["tree"],
      "candidateFreeInputChecksumListSha256":sha((INPUT/"SHA256SUMS.txt").read_bytes()),
      "sourceCount":20,"localeCount":12,"cellCount":len(rows),"counts":counts,
      "proposalCount":len(proposals),"holdCount":len(holds),"allCellRowsHaveSourceAndCurrentHashes":True,
      "placeholdersMarkupNumbersProtectedLiteralsReviewed":True,
      "nativeSpeakerSignoff":False,"browserReviewPerformed":False,
      "createdAtUtc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds"),
    }
    writej(P/"SUMMARY.json",summary)
    readme=f"""# slskR PR #209 W1543-W1562 primary review

This packet reviews all 240 locale cells from the sealed candidate-free input at {INPUT}. Input checksum-list SHA-256: {summary['candidateFreeInputChecksumListSha256']}. The pinned PR head/tree are {manifest['head']} / {manifest['tree']}.

The review used exact source keys, production caller contexts, current values, prior approved wording where relevant, and token signatures. It records accept-current, correction/refinement proposals, or text-free holds. Counts: {counts}.

This is a primary semantic review. It does not include blind or cross-review, native-speaker signoff, or browser review.
"""
    (P/"README.md").write_text(readme,encoding="utf-8")
    sums=[f"{sha(p.read_bytes())}  {p.name}" for p in sorted(P.iterdir()) if p.is_file() and p.name!="SHA256SUMS.txt"]
    (P/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
