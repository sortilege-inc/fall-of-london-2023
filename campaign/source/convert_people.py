#!/usr/bin/env python3
"""
convert_people.py — the owner's Notion character table → the site's people pages.

Reads the Notion export kept beside this repo (never inside it: the export also holds the
Storyteller's prep, and this repo is published):

    ../notion-export/Vampire the Masquerade - Fall of London/
        Fall of London Characters <id>.csv      one row per person — the record
        Character Maps <id>.html                 the owner's grouping of them (the circles)
        Fall of London Characters/<name>/<img>   their portraits

and writes, deterministically (a rerun is byte-identical):

    campaign/docs/heralds/*.md             the four heralds, then the rest of the party
    campaign/docs/dramatis-personae/*.md   everyone else the table may see
    campaign/assets/portraits/*.webp       each person's first-listed picture, 640 px

Every value on a page is the table's own, verbatim: Titles as the epithet, Clan, Affiliations,
Stage of Life, Deceased?, and the Short Note as the page's text. A row whose `Player Visible?`
is not `Yes` is left out. Nothing is added about anyone; a page grows only when someone writes
into it by hand below the generated block (see KEEP_MARK).

    python3 campaign/source/convert_people.py
"""
import csv
import glob
import html
import os
import re
import subprocess
import sys
import unicodedata
from urllib.parse import unquote

CAMPAIGN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(CAMPAIGN)
EXPORT = os.path.join(os.path.dirname(REPO), "notion-export", "Vampire the Masquerade - Fall of London")
DOCS = os.path.join(CAMPAIGN, "docs")
PORTRAITS = os.path.join(CAMPAIGN, "assets", "portraits")

# The four heralds are the player characters (the Notion campaign page's Cast); Doctor Henry
# Banerjee was the fifth, whose player left after the first session (Story So Far, Session 2),
# so the table files him with the Cult of Mithras and so does this.
HERALDS = ["Alice Mockingdale", "Tony Castelli", "Lady Catherine Montague", "Matthias Darkwood"]
PARTY_GROUP = ("The Heralds", "Those who run with them")
# Character Maps' tables, in the order a person is placed by (the first that lists them).
CIRCLES = ["Queen Anne’s Court", "The Cult of Mithras", "Notable Connections", "Mortal Officials"]
# a player-visible person in none of those tables is placed by affiliation
FALLBACK = [("Camarilla", "Queen Anne’s Court")]
OTHERS = "Others met"

# Below this line a page's hand-written text survives a rerun.
KEEP_MARK = "<!-- written by hand below this line; convert_people.py keeps it -->"


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def split(v):
    return [x.strip() for x in v.split(",") if x.strip()]


def circles_from_maps():
    """Character Maps: each <h2> heading then a table of names → {heading: [names]} (the <h4> over each table is only the database's own name)."""
    path = glob.glob(os.path.join(EXPORT, "Character Maps *.html"))[0]
    t = open(path, encoding="utf-8").read()
    out, cur = {}, None
    for m in re.finditer(r"<h[1-3][^>]*>(.*?)</h[1-3]>|<table.*?</table>", t, re.S):
        if m.group(1) is not None:
            cur = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
            continue
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(0), re.S)
        names = []
        for r in rows[1:]:
            cell = re.search(r"<td[^>]*>(.*?)</td>", r, re.S)
            if cell:
                names.append(html.unescape(re.sub(r"<[^>]+>", "", cell.group(1))).strip())
        if cur:
            out.setdefault(cur, []).extend(names)
    return out


def portrait(row, slug):
    pics = [p.strip() for p in row["Picture"].split(",") if p.strip()]
    if not pics:
        return None
    src = os.path.join(EXPORT, *unquote(pics[0]).split("/"))
    if not os.path.isfile(src):
        sys.exit("convert_people: %s: picture %r is not in the export" % (row["Name"], pics[0]))
    rel = "assets/portraits/%s.webp" % slug
    dst = os.path.join(CAMPAIGN, rel)
    if not os.path.isfile(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        subprocess.run(["magick", src + "[0]", "-strip", "-resize", "640x640>", "-quality", "82",
                        "-define", "webp:method=6", dst], check=True)
    return rel


def page(front, body, path):
    lines = ["---"] + ["%s: %s" % (k, v) for k, v in front if v] + ["---", ""]
    text = "\n".join(lines) + (body + "\n" if body else "") + "\n" + KEEP_MARK + "\n"
    if os.path.isfile(path):
        old = open(path, encoding="utf-8").read()
        if KEEP_MARK in old:
            text += old.split(KEEP_MARK, 1)[1].lstrip("\n")
    return text


def main():
    csvp = glob.glob(os.path.join(EXPORT, "Fall of London Characters *.csv"))[0]
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig")))
    maps = circles_from_maps()
    missing = [c for c in CIRCLES if c not in maps]
    if missing:
        sys.exit("convert_people: Character Maps has no table %r" % missing)
    names = {r["Name"] for r in rows}
    for c in CIRCLES:
        for n in maps[c]:
            if n not in names:
                sys.exit("convert_people: Character Maps lists %r in %s, and the table has no such row" % (n, c))
    for n in HERALDS:
        if n not in names:
            sys.exit("convert_people: herald %r is not in the table" % n)

    os.makedirs(PORTRAITS, exist_ok=True)
    written, skipped = {}, []
    order = {}
    for r in rows:
        name = r["Name"]
        if r["Player Visible?"].strip() != "Yes":
            skipped.append(name)
            continue
        affs = split(r["Affiliations"])
        slug = slugify(re.sub(r"\(.*?\)|\[.*?\]", "", name)) or slugify(name)
        if name in HERALDS:
            section, group, idx = "heralds", PARTY_GROUP[0], (1, HERALDS.index(name))
        elif "Party" in affs:
            section, group, idx = "heralds", PARTY_GROUP[1], (2, [x["Name"] for x in rows].index(name))
        else:
            section = "people"
            group = next((c for c in CIRCLES if name in maps[c]), None)
            if group:
                idx = (CIRCLES.index(group) + 1, maps[group].index(name))
            else:
                group = next((g for a, g in FALLBACK if a in affs), OTHERS)
                idx = ((CIRCLES.index(group) + 1) if group in CIRCLES else 9, 100 + [x["Name"] for x in rows].index(name))
        folder = "heralds" if section == "heralds" else "dramatis-personae"
        fn = "%d%03d-%s.md" % (idx[0], idx[1], slug)
        key = "group" if section == "heralds" else "circle"
        front = [
            ("name", name),
            (key, group),
            ("epithet", ", ".join(split(r["Titles"]))),
            ("clan", r["Clan"].strip()),
            ("portrait", portrait(r, slug)),
            ("deceased", "yes" if r["Deceased?"].strip() == "Deceased" else ""),
        ]
        facts = []
        if affs:
            facts.append("**Affiliations:** " + ", ".join(a for a in affs if a != "Party"))
        if r["Stage of Life"].strip():
            facts.append("**Stage of life:** " + r["Stage of Life"].strip())
        body = "\n\n".join(([r["Short Note"].strip()] if r["Short Note"].strip() else []) +
                           ["  \n".join(f for f in facts if not f.endswith(":** "))])
        path = os.path.join(DOCS, folder, fn)
        if path in written:
            sys.exit("convert_people: two people would write %s" % fn)
        written[path] = page(front, body, path)
        order[name] = fn

    # a page on disk that this run did not write is stale: remove it (its hand text included —
    # say so, so a rename is not silent)
    for folder in ("heralds", "dramatis-personae"):
        for old in glob.glob(os.path.join(DOCS, folder, "*.md")):
            if old not in written:
                if KEEP_MARK in open(old, encoding="utf-8").read() and open(old, encoding="utf-8").read().split(KEEP_MARK, 1)[1].strip():
                    sys.exit("convert_people: %s has hand-written text and is no longer generated; move it first" % old)
                os.remove(old)
    for path, text in written.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(text)
    h = sum(1 for p in written if "/heralds/" in p)
    print("convert_people: %d rows · %d heralds and party · %d dramatis personae · %d not player-visible (%s)"
          % (len(rows), h, len(written) - h, len(skipped), ", ".join(skipped)))


if __name__ == "__main__":
    main()
