"""Find drugs whose Phase 2/3 trials were stopped for business/strategic reasons (not safety/efficacy)."""
import json, urllib.request, urllib.parse, csv, re, collections

Q = ("AREA[OverallStatus]TERMINATED AND AREA[StudyType]INTERVENTIONAL AND "
     "AREA[InterventionType]DRUG AND (AREA[Phase]PHASE2 OR AREA[Phase]PHASE3) AND "
     "AREA[LeadSponsorClass]INDUSTRY")
FIELDS = "NCTId,BriefTitle,Phase,LeadSponsorName,WhyStopped,Condition,InterventionName,InterventionType,EnrollmentCount,PrimaryCompletionDate,HasResults"
BIZ = re.compile(r"business|strategic|commercial|portfolio|sponsor decision|company decision|financ|funding|priorit|acqui|merger|bankrupt|corporate|resource|reorgani", re.I)
BAD = re.compile(r"safety|adverse|toxic|futility|efficacy|lack of (benefit|effect)|death|risk|ineffective|interim analysis", re.I)

rows, token = [], None
while True:
    p = {"query.term": Q, "fields": FIELDS, "pageSize": 1000}
    if token: p["pageToken"] = token
    j = json.load(urllib.request.urlopen("https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(p), timeout=60))
    for s in j["studies"]:
        ps = s["protocolSection"]; st = ps.get("statusModule", {})
        why = st.get("whyStopped", "") or ""
        drugs = [i["name"] for i in ps.get("armsInterventionsModule", {}).get("interventions", [])
                 if i.get("type") == "DRUG" and not re.search(r"placebo|saline|standard|vehicle", i["name"], re.I)]
        rows.append({"nct": ps["identificationModule"]["nctId"], "title": ps["identificationModule"].get("briefTitle"),
                     "phase": "/".join(ps.get("designModule", {}).get("phases", [])),
                     "sponsor": ps["sponsorCollaboratorsModule"]["leadSponsor"]["name"], "why": why,
                     "biz": bool(BIZ.search(why)) and not BAD.search(why),
                     "conditions": "; ".join(ps.get("conditionsModule", {}).get("conditions", [])),
                     "drugs": "; ".join(drugs), "n": ps.get("designModule", {}).get("enrollmentInfo", {}).get("count"),
                     "pcd": st.get("primaryCompletionDateStruct", {}).get("date"), "results": s.get("hasResults")})
    token = j.get("nextPageToken"); print(len(rows), flush=True)
    if not token: break

biz = [r for r in rows if r["biz"] and r["drugs"]]
with open("shelved.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(biz)
print("terminated industry P2/3 drug trials", len(rows), "business-stopped", len(biz))
print(collections.Counter(r["sponsor"] for r in biz).most_common(20))
dc = collections.Counter(d.strip().lower() for r in biz for d in r["drugs"].split(";"))
print("distinct drug names", len(dc)); print(dc.most_common(40))
