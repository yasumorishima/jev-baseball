"""Study 4 identity gate: is each saved ja/en article about the player? Rule (registered): a text is kept
only if the article's Wikidata item carries MLB ID (P3541) equal to key_mlbam. Items with no P3541 or
another ID, and pages without a Wikidata item, are dropped. Writes ~/claude-scratch/jev/foreign/identity.json
{lang: {mlbam: [title, qid, [P3541...], verdict]}} with verdict ok / mismatch / no_p3541 / no_item."""
import json, os, time, urllib.error, urllib.parse, urllib.request

J = os.path.expanduser("~/claude-scratch/jev/")
UA = {"User-Agent": "jev-baseball research (github.com/yasumorishima/jev-baseball)"}


def get(u):
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(20 * (a + 1))
    raise RuntimeError("429 persisted")


out = {}
for lang in ("ja", "en"):
    recs = {}
    for f in os.listdir(J + lang + "_text"):
        if f.endswith(".json"):
            d = json.load(open(J + lang + "_text/" + f, encoding="utf-8"))
            recs[d["key_mlbam"]] = d["title"]
    titles = sorted(set(recs.values()))
    qid = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        r = get("https://%s.wikipedia.org/w/api.php?format=json&action=query&prop=pageprops&ppprop=wikibase_item&redirects=1&titles=" % lang
                + urllib.parse.quote("|".join(chunk)))
        q = r["query"]
        back = {}
        for x in q.get("normalized", []) + q.get("redirects", []):
            back[x["to"]] = x["from"]
        for p in q["pages"].values():
            t = p["title"]
            while t in back and t not in chunk:
                t = back[t]
            qid[t] = p.get("pageprops", {}).get("wikibase_item")
        time.sleep(5)
    Q = sorted({v for v in qid.values() if v})
    mlb = {}
    for i in range(0, len(Q), 50):
        r = get("https://www.wikidata.org/w/api.php?format=json&action=wbgetentities&props=claims&maxlag=5&ids=" + "|".join(Q[i:i + 50]))
        for q, e in r["entities"].items():
            mlb[q] = [c["mainsnak"].get("datavalue", {}).get("value") for c in e.get("claims", {}).get("P3541", [])]
        time.sleep(5)
    out[lang] = {}
    for k, t in recs.items():
        q = qid.get(t)
        ids = mlb.get(q, []) if q else []
        v = "no_item" if not q else ("ok" if k in ids else ("no_p3541" if not ids else "mismatch"))
        out[lang][k] = [t, q, ids, v]
    print(lang, {v: sum(1 for x in out[lang].values() if x[3] == v) for v in ("ok", "mismatch", "no_p3541", "no_item")}, flush=True)
tmp = J + "foreign/identity.json.tmp"
json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
os.replace(tmp, J + "foreign/identity.json")
print("done", flush=True)
