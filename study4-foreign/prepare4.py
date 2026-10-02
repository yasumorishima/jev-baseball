"""Study 4 states: the pre-arrival Wikipedia revisions (ja: before Mar 1 of the first NPB year, en: before
Jan 1), cleaned of markup, with the player's own names masked. Text stays on the RPi5 (CC BY-SA, never
committed). Writes ~/claude-scratch/jev/foreign/states.json and prints length and masking checks.
No outcome is read here."""
import html
import csv
import json
import os
import re
import unicodedata

J = os.path.expanduser("~/claude-scratch/jev/")
OUT = J + "foreign/"
os.makedirs(OUT, exist_ok=True)
CAP_JA, CAP_EN = 3000, 6000          # characters kept (beginning of the cleaned body)

TAIL = re.compile(r"^==+\s*(脚注|出典|注釈|関連項目|外部リンク|参考文献|References|Notes|External links|See also|Further reading)\s*==+\s*$",
                  re.M | re.I)


def clean(t):
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"<ref[^>]*?/>", "", t)
    t = re.sub(r"<ref.*?</ref>", "", t, flags=re.S)
    m = TAIL.search(t)
    if m:
        t = t[:m.start()]
    t = re.sub(r"\{\|.*?\|\}", "", t, flags=re.S)
    # year templates carry the dates of the career ({{by|2003}}, {{mlby|2008}}, {{Baseball year|2010}})
    t = re.sub(r"\{\{\s*(?:by|byk|by2|mlby|mlbys|baseball year|by mlb)\s*\|\s*(\d{4})[^{}]*\}\}",
               lambda m: m.group(1) + ("年" if re.search(r"[ぁ-んァ-ン一-龥]", t) else ""), t, flags=re.I)
    prev = None
    while prev != t:                      # nested templates, innermost first
        prev = t
        t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:File|Image|ファイル|画像|Category|カテゴリ):[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]", "", t, flags=re.I)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", t)
    t = re.sub(r"'{2,}", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"^\s*[|!].*$", "", t, flags=re.M)   # stray table/infobox rows
    t = re.sub(r"\n{2,}", "\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


people = {}
for r in csv.DictReader(open(os.path.expanduser("~/claude-scratch/npbmlb/links.csv"), encoding="utf-8")):
    if not r["key_mlbam"]:
        continue
    k = str(int(float(r["key_mlbam"])))
    p = people.setdefault(k, {"first": r["name_first"], "last": r["name_last"], "ja": set()})
    for n in (r["nname"], r["npb_name"]):
        n = unicodedata.normalize("NFKC", n or "").strip()
        if n:
            p["ja"].add(n)
            p["ja"].update(x for x in re.split(r"[・.．\s]", n) if len(x) >= 2)


def mask_ja(t, k, title):
    p = people[k]
    names = set(p["ja"])
    base = re.sub(r"\s*\(.*?\)$", "", title)
    names.add(base)
    names.update(x for x in base.split("・") if len(x) >= 2)
    for n in (p["first"], p["last"]):
        if len(n) >= 3:
            names.add(n)
    for n in sorted(names, key=len, reverse=True):
        t = t.replace(n, "当該選手")
    t = re.sub(r"(当該選手[・=＝\s]*)+", "当該選手", t)
    return t


def mask_en(t, k, title):
    p = people[k]
    t = fold(t)
    base = fold(re.sub(r"\s*\(.*?\)$", "", title))
    parts = {fold(x).lower() for x in (base + " " + p["first"] + " " + p["last"]).replace("-", " ").split() if len(x) >= 3}
    for n in sorted({base, fold(p["first"] + " " + p["last"])}, key=len, reverse=True):
        if " " in n:
            t = re.sub(r"\b%s\b" % re.escape(n), "the player", t)

    def sub(m):
        w = m.group(0)
        b = re.sub(r"'s?$", "", w)
        if b[:1].isupper() and b.lower() in parts:
            return "the player" + ("'s" if w.endswith("'") or w.endswith("'s") else "")
        return w
    t = re.sub(r"[A-Za-z][A-Za-z']*", sub, t)
    t = re.sub(r"(the player\s+)+the player", "the player", t)
    return t


ID = json.load(open(J + "foreign/identity.json", encoding="utf-8"))   # identity gate (idgate4.py)


def load(d, k):
    f = J + d + "/" + k + ".json"
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else None


states, lj, le, leak = {}, [], [], 0
for k in people:
    a, b = load("ja_text", k), load("en_text", k)
    if ID["ja"].get(k, [0, 0, 0, ""])[3] != "ok":
        a = None
    if ID["en"].get(k, [0, 0, 0, ""])[3] != "ok":
        b = None
    if not a and not b:
        continue
    s = {"ja": "", "en": "", "ja_rev": None, "en_rev": None}
    if a:
        c = mask_ja(clean(a["text"]), k, a["title"])
        s["ja_full_len"] = len(c)
        s["ja"] = c[:CAP_JA]
        s["ja_rev"] = [a["revid"], a["timestamp"], a["cutoff"]]
        assert a["timestamp"] < a["cutoff"]
        lj.append(len(s["ja"]))
    if b:
        c = mask_en(clean(b["text"]), k, b["title"])
        s["en_full_len"] = len(c)
        s["en"] = c[:CAP_EN]
        s["en_rev"] = [b["revid"], b["timestamp"], b["cutoff"]]
        assert b["timestamp"] < b["cutoff"]
        le.append(len(s["en"]))
    last = fold(people[k]["last"])
    if len(last) >= 4 and re.search(r"\b%s\b" % re.escape(last), s["en"], re.I):
        leak += 1
    states[k] = s

tmp = OUT + "states.json.tmp"
json.dump(states, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
os.replace(tmp, OUT + "states.json")
q = lambda L: (sorted(L)[len(L) // 2], sorted(L)[len(L) // 4], sorted(L)[3 * len(L) // 4], max(L)) if L else None
print("players with text", len(states), "ja", len(lj), "en", len(le))
print("ja kept chars median/q25/q75/max", q(lj), "en", q(le))
print("en texts still containing the surname", leak)
print("ja capped", sum(1 for x in lj if x >= CAP_JA), "en capped", sum(1 for x in le if x >= CAP_EN))
