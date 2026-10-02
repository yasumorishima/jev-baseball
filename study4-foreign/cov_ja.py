"""Coverage probe (ja.wikipedia): for each NPB foreign player, the latest revision before Mar 1 of the
NPB first year, and the length of its player-characteristics section (選手としての特徴 / プレースタイル).
Counts only."""
import csv, json, re, time, urllib.request, urllib.parse, urllib.error

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

first = {}
name = {}
for r in csv.DictReader(open("/home/yasu/claude-scratch/npbmlb/links.csv", encoding="utf-8")):
    if r["key_mlbam"]:
        k = int(float(r["key_mlbam"]))
        first[k] = min(int(float(r["npb_first_year"])), first.get(k, 9999))
        name[k] = (r["name_first"], r["name_last"], r["nname"])
API = "https://ja.wikipedia.org/w/api.php?format=json&"
SEC = re.compile(r"^==+\s*(選手としての特徴|プレースタイル|特徴)\s*==+\s*$", re.M)
out = {}
for k in sorted(first):
    fn, ln, nn = name[k]
    try:
        s = get(API + "action=query&list=search&srlimit=3&srsearch=" + urllib.parse.quote('"%s %s" 野球' % (fn, ln)))
        title = None
        for h in s["query"]["search"]:
            if nn and nn[:2] in h["title"]:
                title = h["title"]; break
        if not title:
            continue
        ts = "%d-03-01T00:00:00Z" % first[k]
        rv = get(API + "action=query&prop=revisions&rvlimit=1&rvslots=main&rvprop=timestamp|content&rvdir=older&rvstart=%s&titles=%s"
                 % (ts, urllib.parse.quote(title)))
        pg = next(iter(rv["query"]["pages"].values()))
        if "revisions" not in pg:
            out[k] = [title, 0, 0]; continue
        txt = pg["revisions"][0]["slots"]["main"]["*"]
        m = SEC.search(txt)
        sec = 0
        if m:
            rest = txt[m.end():]
            nxt = re.search(r"^==[^=]", rest, re.M)
            sec = len(rest[:nxt.start()] if nxt else rest)
        out[k] = [title, len(txt), sec]
    except Exception as e:
        print("ERR", k, e)
    time.sleep(2.0)
have = [v for v in out.values() if v[1] > 0]
secs = sorted(v[2] for v in have if v[2] > 0)
print("ja title found", len(out), "/", len(first), "pre-arrival revision", len(have),
      "with characteristics section", len(secs), "median section chars", secs[len(secs)//2] if secs else None,
      "section>=200 chars", sum(1 for x in secs if x >= 200))
json.dump({str(k): v for k, v in out.items()}, open("/home/yasu/claude-scratch/jev/foreign_cov_ja.json", "w"), ensure_ascii=False)
