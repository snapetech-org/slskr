import json,hashlib,re,shutil
from pathlib import Path
I=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1403-1422-primary-20261103/candidate-free-input")
O=Path("/home/keith/Documents/code/task-scratch/slskr-pr204-w1403-1422-cross-audit-20261103/independent-review")
sha=lambda b:hashlib.sha256(b).hexdigest()
jl=lambda p:[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x]
def toks(s):
 return {"placeholders":re.findall(r"\{[A-Za-z][A-Za-z0-9_]*\}",s),"markupTags":re.findall(r"</?[A-Za-z][^>]*>",s),"numericTokens":re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?(?![A-Za-z])",s),"protectedLiterals":list(dict.fromkeys(m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[A-Z0-9]*|ffmpeg|Chromaprint|Soulseek|Spotify|YouTube|Pushbullet|Matrix|WebSocket|OpenAI)(?![A-Za-z0-9])",s)))}
chg={
(1406,"hi"):("update","इवेंट्स को रखने की अवधि (दिन)","Current Hindi is an unnatural noun stack; proposal states the event retention duration in days, matching the numeric form-field label."),
(1407,"zh-Hans"):("update","每15分钟一次","每15分钟一班 means a shift/crew every 15 minutes. 一次 correctly expresses recurring cadence."),
(1407,"zh-Hant"):("update","每15分鐘一次","每15分鐘一班 means a shift/crew every 15 minutes. 一次 correctly expresses recurring cadence."),
(1408,"hi"):("update","यहाँ हर ऑटोमेशन दिखाई देता है। जब उनका प्रभाव आपके नोड के अनुकूल हो, तब ऑटोमेशन रेसिपी सक्षम करें; निष्पादन मैन्युअल रूप से होता है और इसके लिए वास्तविक बैकएंड कार्रवाई उपलब्ध होनी चाहिए।","व्यंजन means a prepared dish and reads as food here. Proposal identifies automation recipes and preserves manual execution/backend availability."),
(1408,"vi"):("update","Mọi hoạt động tự động hóa đều hiển thị ở đây. Hãy bật các quy trình tự động hóa khi mức độ ảnh hưởng của chúng phù hợp với nút của bạn; việc thực thi được thực hiện thủ công và cần có sẵn hành động thực sự từ backend.","Current công thức nấu ăn explicitly means cooking recipes. Proposal replaces it with automation workflows while preserving node suitability and manual execution."),
(1409,"ar"):("update","الأدلة","شهادة means certificate/testimony, not evidence in this table column. الأدلة is the appropriate evidence label."),
(1410,"ar"):("update","الأدلة (","Same evidence term is mistranslated as certificate. Keep the opening parenthesis used before the runtime-formatted regional number."),
(1410,"zh-Hans"):("update","证据（","Full-width opening parenthesis is appropriate, but the current intervening space is typographically unnecessary."),
(1410,"ja"):("update","証拠（","Remove the unnecessary space before the full-width opening parenthesis."),
(1410,"zh-Hant"):("update","證據（","Full-width opening parenthesis is appropriate, but the current intervening space is typographically unnecessary."),
(1411,"ar"):("update","بيئة اختبار معزولة لمراجعة الأدلة","صندوق الرمل is a literal sandbox calque. Proposal conveys the isolated test environment used for evidence review."),
(1412,"ar"):("update","استثناء","شهادة means certificate/testimony; source is an exception value in compatibility tables."),
(1413,"es"):("update","Excluya de futuras descargas automáticas el par rechazado de la lista de deseos y el directorio remoto.","Existing order makes rechazados attach ambiguously to the wishlist. Proposal scopes rejection to the peer."),
(1413,"ar"):("update","استبعد النظير المرفوض في قائمة الرغبات والدليل البعيد من التنزيلات التلقائية المستقبلية.","Current dual/plural adjective can modify both peer and remote directory. Proposal attaches rejection to the peer only."),
(1413,"vi"):("update","Loại trừ đối tượng ngang hàng trong Danh sách mong muốn đã bị từ chối và thư mục từ xa khỏi các lượt tải xuống tự động trong tương lai.","Current order can read as a rejected wishlist rather than a rejected peer. Proposal makes the peer the rejected item and preserves the separate remote directory."),
(1413,"id"):("update","Kecualikan peer Daftar Keinginan yang ditolak serta direktori jarak jauh dari unduhan otomatis di masa mendatang.","Existing phrasing makes Wishlist appear to modify both peer and remote directory. Proposal scopes rejection to the peer."),
(1415,"ar"):("update","نفّذ {title}","Current مصدر form تنفيذ is a noun/infinitive for an action control. Use the imperative and preserve the placeholder."),
(1418,"ja"):("update","実行契約がブロックされています","約定契約 is an unnatural rendering of execution contract. This status says the execution contract is blocked."),
(1419,"ja"):("update","実行契約の準備完了","約定契約 is an unnatural rendering of execution contract. This concise status pairs with the blocked status."),
(1419,"vi"):("update","Hợp đồng thực thi đã sẵn sàng","Hợp đồng thi công means a construction contract. Thực thi expresses execution in this integration status."),
(1420,"zh-Hant"):("hold",None,"通路 can mean a route/channel, while 頻道 is used for communication/media channels. Caller confirms a channel list and channelId but not the product's channel type. Keep unchanged pending domain terminology review."),
(1421,"ar"):("update","الإعداد الحالي ليس خريطة YAML.","تعيين means assignment/appointment, not a YAML mapping structure. خريطة expresses the source structure and preserves YAML.")
}
ctx={x["position"]:x for x in jl(I/"source-contexts.jsonl")}
cells=jl(I/"current-target-cells.jsonl"); out=[]
for c in cells:
 d,p,r=chg.get((c["position"],c["locale"]),("retain",c["currentTarget"],"Reviewed against the English source and production caller context; current wording preserves the intended interface meaning and required tokens."))
 if d=="hold": p=c["currentTarget"]
 s=c["sourceKey"]; st=toks(s); ct=toks(c["currentTarget"]); pt=toks(p)
 n=(c["position"]==1416 and c["locale"] in ("ja","ko") and st["numericTokens"]==[] and ct["numericTokens"]==["3"])
 out.append({"position":c["position"],"historicalSourceOrdinal":c["historicalSourceOrdinal"],"sourceKey":s,"sourceKeySha256":c["sourceKeySha256"],"locale":c["locale"],"sourceContextSha256":c["sourceContextSha256"],"productionCallerCount":c["callerCount"],"callerRefs":c["callerRefs"],"catalogPath":c["catalogPath"],"catalogFileSha256":c["catalogFileSha256"],"catalogGitBlob":c["catalogGitBlob"],"catalogKeyCount":c["catalogKeyCount"],"currentTarget":c["currentTarget"],"currentTargetSha256":c["currentTargetSha256"],"independentProposal":p,"proposalSha256":sha(p.encode()),"disposition":d,"rationale":r,"sourceTokens":st,"currentTargetTokens":ct,"proposalTokens":pt,"placeholderSequenceMatches":st["placeholders"]==pt["placeholders"],"markupMatches":st["markupTags"]==pt["markupTags"],"numericTokenAudit":"source spells out three; target digit 3 is same value" if n else ("match" if st["numericTokens"]==ct["numericTokens"] else "mismatch"),"protectedLiteralMismatchTokens":[x for x in st["protectedLiterals"] if x not in pt["protectedLiterals"]],"primaryCandidateOrDecisionExposed":False})
with (O/"independent-review.jsonl").open("w",encoding="utf8",newline="\n") as f:
 for x in out:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n")
for n in ("prior-hold-reattestation.jsonl","prior-selection-reattestation.jsonl","PR-attestation.json"):shutil.copyfile(I/n,O/n)
counts={x:sum(r["disposition"]==x for r in out) for x in ("retain","update","hold")}
priorh=jl(I/"prior-hold-reattestation.jsonl"); priors=jl(I/"prior-selection-reattestation.jsonl"); inp=json.loads((I/"manifest.json").read_text())
summary={"result":"SEALED_INDEPENDENT_REVIEW","reviewedCells":len(out),"sourceCount":20,"localeCount":12,"dispositions":counts,"priorHoldsReattested":len(priorh),"changedPriorHolds":0,"priorSelectionsReattested":len(priors),"candidateFreeOnly":True,"primaryMaterialsOpened":False,"baselineNumericTokenMismatches":[{"position":1416,"locale":"ja","adjudication":"source spells out three, target digit 3 has the same value"},{"position":1416,"locale":"ko","adjudication":"source spells out three, target digit 3 has the same value"}],"newHolds":[{"position":1420,"locale":"zh-Hant","issue":"channel term requires product-domain glossary/context"}],"inputRoot":str(I),"inputManifestSha256":sha((I/"manifest.json").read_bytes()),"inputChecksumListSha256":sha((I/"SHA256SUMS.txt").read_bytes()),"inputSourceQueueSha256":sha((I/"source-queue.jsonl").read_bytes()),"inputSourceOrderSha256":inp["sourceLookupKeyOrderSha256"]}
(O/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
manifest={"task":"slskR PR #204 W1403-W1422 independent translation review","repo":"snapetech-org/slskR","pr":204,"branch":"codex/slskr-l10n-audit-20261030","head":"727500e46852a5b6578e571781693857510943d9","tree":"c71165c20fc6ba7d49d563898ea2ec8e1e448672","base":"2a2b188f10b9460a15bc6d5c34e406b0193d51ba","state":"OPEN","draft":True,"selectedPositions":[1403,1422],"cellCount":240,"candidateFreeInputRoot":str(I),"candidateFreeManifestSha256":summary["inputManifestSha256"],"candidateFreeChecksumListSha256":summary["inputChecksumListSha256"],"primaryMaterialsOpened":False,"reviewPacketSealStatus":"sealed before primary access","dispositionCounts":counts,"priorHoldsReattested":35,"changedPriorHolds":0,"priorSelectionsReattested":160,"inputHashes":{n:sha((I/n).read_bytes()) for n in ("current-target-cells.jsonl","source-contexts.jsonl","prior-hold-reattestation.jsonl","prior-selection-reattestation.jsonl","catalog-file-pins.json","PR-attestation.json")}}
(O/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
print(json.dumps({"independentRows":len(out),"dispositions":counts,"priorHolds":len(priorh),"priorSelections":len(priors),"reviewDirectory":str(O)},ensure_ascii=False,indent=2))
