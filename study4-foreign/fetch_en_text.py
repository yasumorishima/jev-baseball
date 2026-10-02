"""Save the en.wikipedia revision just before Jan 1 of each player's NPB first year (titles from foreign_cov_en.json).
Text stays on the RPi5 (CC BY-SA, never committed). Resumable. Then prints a keyword census."""
import csv, json, os, re, time, urllib.request, urllib.parse, urllib.error

D = "/home/yasu/claude-scratch/jev/en_text"
os.makedirs(D, exist_ok=True)
UA = {"User-Agent": "jev-baseball research (github.com/yasumorishima/jev-baseball)"}
def get(u):
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(30 * (a + 1))
    raise RuntimeError("429 persisted")

first = {}
for r in csv.DictReader(open("/home/yasu/claude-scratch/npbmlb/links.csv", encoding="utf-8")):
    if r["key_mlbam"]:
        k = str(int(float(r["key_mlbam"])))
        first[k] = min(int(float(r["npb_first_year"])), first.get(k, 9999))
W = json.load(open("/home/yasu/claude-scratch/jev/foreign_cov_en.json", encoding="utf-8"))["wiki"]
API = "https://en.wikipedia.org/w/api.php?format=json&"
n = 0
for k, v in sorted(W.items()):
    if not v or v[1] <= 0: continue
    f = os.path.join(D, k + ".json")
    if os.path.exists(f): continue
    ts = "%d-01-01T00:00:00Z" % first[k]
    try:
        rv = get(API + "action=query&prop=revisions&rvlimit=1&rvslots=main&rvprop=ids|timestamp|content&rvdir=older&rvstart=%s&titles=%s"
                 % (ts, urllib.parse.quote(v[0])))
        pg = next(iter(rv["query"]["pages"].values()))
        r0 = pg["revisions"][0]
        rec = dict(key_mlbam=k, title=v[0], cutoff=ts, revid=r0["revid"], timestamp=r0["timestamp"], text=r0["slots"]["main"]["*"])
        tmp = f + ".tmp"
        json.dump(rec, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(tmp, f)
        n += 1
    except Exception as e:
        print("ERR", k, e, flush=True)
    time.sleep(2.0)
print("saved this run", n, "total files", len([x for x in os.listdir(D) if x.endswith(".json")]), flush=True)

KW = {
    "velocity": r"\bmph\b|fastball|velocity|miles per hour",
    "pitches": r"slider|curveball|changeup|splitter|cutter|sinker|two-seam|knuckle",
    "control": r"\bcontrol\b|command|walk rate|\bwalks\b",
    "power": r"\bpower\b|home run power|raw power",
    "contact": r"contact|plate discipline|strikeouts? (?:rate|prone)|batting eye",
    "defense": r"defens|\barm\b|glove|range",
    "speed": r"\bspeed\b|stolen bases?|baserunn",
    "makeup": r"work ethic|makeup|personality|leadership",
    "scouting": r"scouting|scouts?\b|prospect|Baseball America|MLB\.com",
    "japan": r"Japan|NPB|Nippon Professional",
}
cnt = {k: 0 for k in KW}; lens = []
files = [x for x in os.listdir(D) if x.endswith(".json")]
for x in files:
    t = json.load(open(os.path.join(D, x), encoding="utf-8"))["text"]
    body = re.sub(r"\{\|.*?\|\}", "", t, flags=re.S)
    body = re.sub(r"\{\{[^{}]*\}\}", "", body)
    body = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", body, flags=re.S)
    lens.append(len(body))
    for k, p in KW.items():
        if re.search(p, body, flags=re.I): cnt[k] += 1
lens.sort()
print("files", len(files), "body chars median", lens[len(lens)//2] if lens else None,
      "q25", lens[len(lens)//4] if lens else None, "q75", lens[3*len(lens)//4] if lens else None, flush=True)
print("articles containing:", cnt, flush=True)
