"""Direction-of-effect filter: does the drug push the target the way human genetics says the disease needs?"""
import json, urllib.request, csv, collections, os, re
from concurrent.futures import ThreadPoolExecutor

URL = "https://api.platform.opentargets.org/api/v4/graphql"
CACHE = "cache_dir.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
Q = ('query($d:String!,$t:String!){disease(efoId:$d){evidences(ensemblIds:[$t],size:300){rows{datasourceId '
     'directionOnTarget directionOnTrait score}}}}')

def ev(pair):
    k = "|".join(pair)
    if k in cache: return cache[k]
    r = urllib.request.Request(URL, json.dumps({"query": Q, "variables": {"d": pair[1], "t": pair[0]}}).encode(),
                               {"Content-Type": "application/json"})
    for _ in range(3):
        try:
            rows = ((json.load(urllib.request.urlopen(r, timeout=90)).get("data") or {}).get("disease") or {})
            rows = ((rows.get("evidences") or {}).get("rows")) or []
            cache[k] = rows; return rows
        except Exception:
            pass
    return None

DOWN = re.compile(r"INHIBITOR|ANTAGONIST|NEGATIVE|BLOCKER|INVERSE|DEGRADER|DISRUPTING", re.I)
UP = re.compile(r"AGONIST|ACTIVATOR|POSITIVE|OPENER|STABILISER|EXOGENOUS|ENHANCER", re.I)

def drug_dir(action):
    acts = [a for a in action.split("; ") if a]
    up = any(UP.search(a) and not re.search("ANTAGONIST|INVERSE", a, re.I) for a in acts)
    down = any(DOWN.search(a) for a in acts)
    return "up" if up and not down else "down" if down and not up else "?"

m = list(csv.DictReader(open("matches.csv", encoding="utf-8")))
pairs = sorted({(r["target_id"], r["disease_id"]) for r in m})
with ThreadPoolExecutor(6) as ex:
    res = dict(zip(pairs, ex.map(ev, pairs)))
json.dump(cache, open(CACHE, "w"))

for r in m:
    rows = res.get((r["target_id"], r["disease_id"])) or []
    need = collections.Counter()
    for e in rows:
        t, tr, s = e.get("directionOnTarget"), e.get("directionOnTrait"), e.get("score") or 0
        if t not in ("GoF", "LoF") or tr not in ("risk", "protect"): continue
        need["down" if (t == "GoF") == (tr == "risk") else "up"] += s
    tot = sum(need.values())
    r["need"] = (need.most_common(1)[0][0] if tot else "?")
    r["need_conf"] = round(need[r["need"]] / tot, 2) if tot else 0
    r["need_n"] = round(tot, 1)
    r["drug_dir"] = drug_dir(r["action"])
    r["verdict"] = ("MATCH" if r["need"] == r["drug_dir"] and r["need_conf"] >= 0.75
                    else "WRONG" if r["need"] != "?" and r["drug_dir"] != "?" and r["need"] != r["drug_dir"] and r["need_conf"] >= 0.75
                    else "unclear")

with open("directed.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(m[0])); w.writeheader(); w.writerows(m)
print(collections.Counter(r["verdict"] for r in m))
ok = sorted([r for r in m if r["verdict"] == "MATCH"], key=lambda r: (-float(r["genetic_score"]) * r["need_conf"]))
seen = set()
for r in ok:
    if (r["drug"], r["new_disease"][:25]) in seen: continue
    seen.add((r["drug"], r["new_disease"][:25]))
    print(f'{r["drug"][:20]:20} {r["stage"]:9} {r["drug_dir"]:4} {r["target"]:8} -> {r["new_disease"][:60]:60} g={r["genetic_score"]} conf={r["need_conf"]} n={r["need_n"]}')
