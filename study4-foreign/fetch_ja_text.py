"""Save the ja.wikipedia revision just before Mar 1 of each player's NPB first year (titles from foreign_cov_ja.json).
Text stays on the RPi5 (CC BY-SA, never committed). One JSON per player: revid, timestamp, title, wikitext.
Resumable: skips players already saved. Then prints a keyword census (career-only vs evaluative)."""
import csv, json, os, re, time, urllib.request, urllib.parse, urllib.error

D = "/home/yasu/claude-scratch/jev/ja_text"
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
J = json.load(open("/home/yasu/claude-scratch/jev/foreign_cov_ja.json", encoding="utf-8"))
API = "https://ja.wikipedia.org/w/api.php?format=json&"
n = 0
for k, v in sorted(J.items()):
    if not v or v[1] <= 0: continue
    f = os.path.join(D, k + ".json")
    if os.path.exists(f): continue
    ts = "%d-03-01T00:00:00Z" % first[k]
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

# keyword census on body text (markup roughly stripped)
KW = {
    "velocity": r"球速|km/h|マイル|速球|直球",
    "pitches": r"スライダー|カーブ|チェンジアップ|スプリット|カットボール|シンカー|ツーシーム|変化球",
    "control": r"制球|コントロール|四球",
    "power": r"長打力|パワー|本塁打を量産|飛距離",
    "contact": r"ミート|確実性|選球眼|三振が多",
    "defense_speed": r"守備|肩|俊足|走塁|盗塁",
    "makeup": r"性格|人柄|真面目|練習熱心|陽気",
    "npb_signing": r"契約|入団|獲得",
}
cnt = {k: 0 for k in KW}; lens = []
files = [x for x in os.listdir(D) if x.endswith(".json")]
for x in files:
    t = json.load(open(os.path.join(D, x), encoding="utf-8"))["text"]
    body = re.sub(r"\{\|.*?\|\}", "", t, flags=re.S)        # tables
    body = re.sub(r"\{\{[^{}]*\}\}", "", body)               # simple templates
    body = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", body, flags=re.S)
    lens.append(len(body))
    for k, p in KW.items():
        if re.search(p, body): cnt[k] += 1
lens.sort()
print("files", len(files), "body chars median", lens[len(lens)//2] if lens else None,
      "q25", lens[len(lens)//4] if lens else None, "q75", lens[3*len(lens)//4] if lens else None, flush=True)
print("articles containing:", cnt, flush=True)
