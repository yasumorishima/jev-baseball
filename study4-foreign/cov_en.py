"""Coverage probe: which pre-arrival text sources exist for the NPB foreign players (links.csv).
Sources: (a) StatsAPI draft blurb (draft year from people.draftYear), (b) English Wikipedia
revision dated before Jan 1 of the NPB first year. Counts only; no text is kept."""
import csv, json, time, urllib.request, urllib.parse, urllib.error

UA = {"User-Agent": "jev-baseball coverage probe (github.com/yasumorishima/jev-baseball)"}
def get(u):
    for a in range(5):
        req = urllib.request.Request(u, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(30 * (a + 1))
    raise RuntimeError("429 persisted")

rows = {}
for r in csv.DictReader(open("/home/yasu/claude-scratch/npbmlb/links.csv", encoding="utf-8")):
    if r["key_mlbam"]:
        k = int(float(r["key_mlbam"]))
        fy = int(float(r["npb_first_year"]))
        rows[k] = min(fy, rows.get(k, 9999))
ids = sorted(rows)
print("players", len(ids))

people = {}
for i in range(0, len(ids), 100):
    d = get("https://statsapi.mlb.com/api/v1/people?personIds=" + ",".join(map(str, ids[i:i+100])))
    for p in d["people"]:
        people[p["id"]] = p
dy = {k: people[k].get("draftYear") for k in ids if k in people}
print("with draftYear", sum(1 for v in dy.values() if v))

blurb = {}  # draft blurbs measured 2026-10-02: 3 / 311, not re-fetched

# Wikipedia: search title by full name + baseball, then revision before Jan 1 of NPB first year
wiki = {}
for k in ids:
    p = people.get(k)
    if not p: continue
    q = p["fullName"] + " baseball"
    try:
        s = get("https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=1&srsearch=" + urllib.parse.quote(q))
        hits = s["query"]["search"]
        if not hits: continue
        title = hits[0]["title"]
        if p.get("lastName", "").split()[-1].lower() not in title.lower(): continue
        ts = "%d-01-01T00:00:00Z" % rows[k]
        rv = get("https://en.wikipedia.org/w/api.php?action=query&prop=revisions&format=json&rvlimit=1&rvprop=timestamp|size&rvstart=%s&rvdir=older&titles=%s" % (ts, urllib.parse.quote(title)))
        pg = next(iter(rv["query"]["pages"].values()))
        if "revisions" in pg:
            wiki[k] = (title, pg["revisions"][0]["size"])
    except Exception as e:
        print("wiki ERR", k, e)
    time.sleep(2.0)
    if len(wiki) % 10 == 0:
        json.dump({str(kk): v for kk, v in wiki.items()}, open("/home/yasu/claude-scratch/jev/foreign_cov_en.partial.json", "w"))
sizes = sorted(v[1] for v in wiki.values())
print("wiki pre-arrival revision", len(wiki), "/", len(ids),
      "median bytes", sizes[len(sizes)//2] if sizes else None,
      ">=3000 bytes", sum(1 for s in sizes if s >= 3000))
json.dump({"blurb": {str(k): v for k, v in blurb.items()}, "wiki": {str(k): v for k, v in wiki.items()},
           "first_year": {str(k): v for k, v in rows.items()}},
          open("/home/yasu/claude-scratch/jev/foreign_cov_en.json", "w"))
