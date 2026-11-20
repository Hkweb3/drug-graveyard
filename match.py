"""Shelved (never-approved) drugs x human-genetic evidence for NEW diseases, via Open Targets."""
import json, urllib.request, urllib.error, csv, re, collections, os
from concurrent.futures import ThreadPoolExecutor

URL = "https://api.platform.opentargets.org/api/v4/graphql"
CACHE = "cache.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def gql(q, v=None):
    k = q + json.dumps(v or {}, sort_keys=True)
    if k in cache: return cache[k]
    r = urllib.request.Request(URL, json.dumps({"query": q, "variables": v or {}}).encode(), {"Content-Type": "application/json"})
    for _ in range(3):
        try:
            out = json.load(urllib.request.urlopen(r, timeout=60)); cache[k] = out; return out
        except Exception as e:
            err = e
    return {"error": str(err)}

SEARCH = 'query($q:String!){search(queryString:$q,entityNames:["drug"],page:{index:0,size:1}){hits{id name}}}'
DRUG = ('query($id:String!){drug(chemblId:$id){id name drugType maximumClinicalStage drugWarnings{warningType} '
        'mechanismsOfAction{rows{mechanismOfAction actionType targets{id approvedSymbol}}} indications{rows{disease{id name}}}}}')
TGT = ('query($id:String!){target(ensemblId:$id){approvedSymbol associatedDiseases(page:{index:0,size:60}){rows{score '
       'disease{id name} datatypeScores{id score}}}}}')

shelved = list(csv.DictReader(open("shelved.csv", encoding="utf-8")))
name2trials = collections.defaultdict(list)
for r in shelved:
    for d in r["drugs"].split(";"):
        d = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|ug|ml)\b", "", d, flags=re.I).strip()
        if len(d) > 2: name2trials[d.lower()].append(r)

def resolve(name):
    h = gql(SEARCH, {"q": name}).get("data", {}) or {}
    hits = (h.get("search") or {}).get("hits") or []
    if not hits: return None
    d = (gql(DRUG, {"id": hits[0]["id"]}).get("data") or {}).get("drug")
    return d

with ThreadPoolExecutor(6) as ex:
    drugs = dict(zip(name2trials, ex.map(resolve, name2trials)))
stages = collections.Counter((d or {}).get("maximumClinicalStage") for d in drugs.values())
print("stages", stages)

APPROVED = {"APPROVAL", "PHASE_4", "APPROVED"}
cand = {}
for n, d in drugs.items():
    if not d or d.get("maximumClinicalStage") in APPROVED: continue
    if d.get("drugWarnings"): continue  # withdrawn / black box etc.
    cand.setdefault(d["id"], {"drug": d, "names": set(), "trials": []})
    cand[d["id"]]["names"].add(n); cand[d["id"]]["trials"] += name2trials[n]
print("never-approved shelved drugs", len(cand))

tids = {t["id"] for c in cand.values() for m in ((c["drug"].get("mechanismsOfAction") or {}).get("rows") or []) for t in m["targets"]}
with ThreadPoolExecutor(6) as ex:
    tg = dict(zip(tids, ex.map(lambda t: (gql(TGT, {"id": t}).get("data") or {}).get("target"), tids)))
json.dump(cache, open(CACHE, "w"))

out = []
for cid, c in cand.items():
    d = c["drug"]; rows = (d.get("mechanismsOfAction") or {}).get("rows") or []
    tlist = [t for m in rows for t in m["targets"]]
    if not tlist or len({t["id"] for t in tlist}) > 8: continue  # skip promiscuous
    known = {x["disease"]["name"].lower() for x in (d.get("indications") or {}).get("rows", [])}
    known |= {w.strip().lower() for t in c["trials"] for w in t["conditions"].split(";")}
    best = {}
    for t in tlist:
        T = tg.get(t["id"]) or {}
        for a in (T.get("associatedDiseases") or {}).get("rows", []):
            g = {x["id"]: x["score"] for x in a["datatypeScores"]}.get("genetic_association", 0)
            dn = a["disease"]["name"]
            if g < 0.6 or dn.lower() in known: continue
            if re.search(r"neoplasm|cancer|carcinoma|tumou?r|measurement|disease$", dn, re.I) and len(dn) < 12: continue
            if dn not in best or g > best[dn][0]: best[dn] = (g, t["approvedSymbol"], t["id"], a["disease"]["id"])
    for dn, (g, sym, tid, did) in best.items():
        out.append({"drug": d["name"], "chembl": cid, "type": d.get("drugType"), "stage": d.get("maximumClinicalStage"),
                    "moa": "; ".join(sorted({m["mechanismOfAction"] for m in rows})),
                    "action": "; ".join(sorted({m.get("actionType") or "" for m in rows})),
                    "target": sym, "target_id": tid, "disease_id": did, "new_disease": dn, "genetic_score": round(g, 3),
                    "sponsor": c["trials"][0]["sponsor"], "why_stopped": c["trials"][0]["why"][:200],
                    "old_conditions": c["trials"][0]["conditions"][:150], "nct": c["trials"][0]["nct"]})
out.sort(key=lambda r: -r["genetic_score"])
with open("matches.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print("matches", len(out), "drugs with >=1 match", len({r["drug"] for r in out}))
