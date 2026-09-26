#!/usr/bin/env python3
"""
check_absorb.py — proves campaign/pack/seed.json carries the owner's Notion GM pages word for word
(PLAYBOOK §4b.2's "independent every-word check").

For each page it reads the export's HTML its own way — every word in the page body, the table of
contents dropped, nothing else — and compares that multiset of words with the words of the seed's
sections that came from the page. The seed's own additions are removed first, each by a declared
rule: an image's link ("[Image: file](path)"), a link's target, the list-depth mark "↳", the column
names a database row is written with, and the players' names (absorb_notion.PLAYER_NAMES). Anything
missing or extra after that fails, naming the word and the page.

The characters table is checked cell by cell: every non-empty cell of every row is in that
person's section.

    python3 campaign/source/check_absorb.py
"""
import collections
import csv
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import absorb_notion as A  # noqa: E402  (paths and PLAYER_NAMES only)

WORD = re.compile(r"[0-9A-Za-zÀ-ÿ'Ā-ɏ]+")


def page_words(path):
    t = open(path, encoding="utf-8").read()
    t = t[t.index('<div class="page-body"'):]
    t = re.sub(r"<nav\b.*?</nav>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return collections.Counter(WORD.findall(html.unescape(t).replace("’", "'")))


def seed_words(texts, headers=()):
    s = " ".join(texts)
    s = re.sub(r"\[Image: [^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\([^)]*\)", r"\1", s)
    for h in headers:
        s = s.replace(" · %s: " % h, " · ")
    for old, new in A.PLAYER_NAMES:
        s = s.replace(new, old)
    s = s.replace("↳", " ")
    return collections.Counter(WORD.findall(s.replace("’", "'")))


def flat(sec):
    out = [sec.get("title", ""), sec.get("text", "")]
    for s in sec.get("sections") or []:
        out += flat(s)
    return out


def main():
    seed = json.load(open(A.OUT, encoding="utf-8"))
    ov = {s["id"]: s for s in seed["gm"]["overview"]}
    fails = []

    def compare(name, want, got):
        miss, extra = want - got, got - want
        if miss or extra:
            fails.append("%s: missing %s · extra %s" % (name, dict(miss.most_common(12)), dict(extra.most_common(12))))
        print("  %-26s %6d words · %s" % (name, sum(want.values()), "OK" if not (miss or extra) else "FAIL"))

    story = A.page("Fall of London The Story So Far *.html")
    # the page's own <h2> titles are the cards' titles; Session Zero is an overview section
    texts = flat(ov["fol-session-zero"]) + [t for c in seed["arc"] for t in flat(c)]
    compare("The Story So Far", page_words(story), seed_words(texts))

    compare("Prep Notes", page_words(A.page("Prep Notes *.html")), seed_words(flat(ov["fol-prep-notes"])[1:]))  # its title is the page's

    maps = A.page("Character Maps *.html")
    heads = set()
    for tb in re.findall(r"<table.*?</table>", open(maps, encoding="utf-8").read(), re.S):
        heads |= {html.unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)}
    compare("Character Maps", page_words(maps), seed_words(flat(ov["fol-character-maps"])[1:], sorted(heads, key=len, reverse=True)))

    compare("Rules Quickreference", page_words(A.page("Rules Quickreference *.html")),
            seed_words([t for s in seed["gm"]["rules"] for t in flat(s)]))

    rows = list(csv.DictReader(open(A.page("Fall of London Characters *.csv"), encoding="utf-8-sig")))
    people = {p["title"]: p["text"] for p in seed["gm"]["people"]}
    cells = 0
    for r in rows:
        txt = people.get(r["Name"])
        if txt is None:
            fails.append("characters: %r has no section" % r["Name"])
            continue
        for c, v in r.items():
            if c in ("Name", "Picture") or not v.strip():
                continue
            cells += 1
            if "**%s:** %s" % (c, v.strip()) not in txt:
                fails.append("characters: %s: %s %r not carried" % (r["Name"], c, v))
        for pic in [p for p in r["Picture"].split(",") if p.strip()]:
            cells += 1
            if "[Image: %s]" % os.path.basename(A.unquote(pic.strip())) not in txt:
                fails.append("characters: %s: picture %r not linked" % (r["Name"], pic))
    print("  %-26s %6d rows · %d cells · %s" % ("Characters table", len(rows), cells, "OK" if not any(f.startswith("characters") for f in fails) else "FAIL"))
    if len(people) != len(rows):
        fails.append("characters: %d sections for %d rows" % (len(people), len(rows)))

    # every image the seed links is on disk
    for m in re.finditer(r"\]\((campaign/assets/gm/[^)]+)\)", json.dumps(seed, ensure_ascii=False)):
        if not os.path.isfile(os.path.join(A.REPO, m.group(1))):
            fails.append("image %s is linked and not on disk" % m.group(1))

    if fails:
        print("check_absorb: FAILED")
        for f in fails:
            print("  " + f)
        return 1
    print("check_absorb: OK — every word of the five GM pages and every cell of the characters table is in the seed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
