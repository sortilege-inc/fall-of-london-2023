#!/usr/bin/env python3
"""
absorb_notion.py — the owner's Notion workspace for the chronicle → the GM tabs' seed
(campaign/pack/seed.json), moved once and whole (PLAYBOOK §4b.2: the GM's material lives in the
GM tabs, in the pack; owner, 2026-09-25: "GM notes should all be available in the GM section").

Reads the export kept beside this repo (../notion-export/, never committed) and writes:

  gm.overview   The campaign (the Notion page's own properties, player names left out — see
                PLAYER_NAMES), Session Zero, Prep Notes, Character Maps
  arc           The Story So Far, one card per session (<h2>), its <h3>s as beats — all marked
                played; the Storyteller's raw notes, verbatim
  gm.rules      Rules Quickreference
  gm.people     every row of the characters table, player-visible or not, every column
  campaign/assets/gm/   the pages' images (the book's handouts), linked where they stood
  party         the heralds' character files (campaign/characters/*.json, written from the book
                by convert_pregens.py), as Coterie members with fixed ids — the table opens with
                them; the seed never re-adds one the GM removed

Text is verbatim: each block's words are the page's, in the GM text's small Markdown (**bold**,
*italic*, `- ` lists, `> ` quotes, [links](…)). Nested list depth, which that Markdown does not
draw, is kept as a leading "↳". Every page is proven word for word by check_absorb.py, which
reads the HTML its own way.

Ids are fixed (`fol-…`, from the heading), so the seed can grow and never re-offers what the GM
removed (engine/state.js seed).

    python3 campaign/source/absorb_notion.py
"""
import csv
import glob
import html
import json
import os
import re
import subprocess
import sys
import unicodedata
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notion  # noqa: E402

CAMPAIGN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(CAMPAIGN)
ROOT = os.path.join(os.path.dirname(REPO), "notion-export")
EXPORT = os.path.join(ROOT, "Vampire the Masquerade - Fall of London")
OUT = os.path.join(CAMPAIGN, "pack", "seed.json")
IMG_DIR = os.path.join(CAMPAIGN, "assets", "gm")
PACK_KIND = "sortilege-vtt-campaign"  # engine/state.js PACK_KIND

# The repo is public, so the seed is too: the players' names and handles stay out of it. The
# campaign page's Players property is not carried, its Cast is carried without the player before
# each character, and the one mention in the notes is replaced. Each entry must apply (a stale
# entry fails the run).
PLAYER_NAMES = [("Going forward shai will be 30m late", "Going forward [a player] will be 30m late")]


def page(pattern):
    hits = glob.glob(os.path.join(EXPORT, pattern)) or glob.glob(os.path.join(ROOT, pattern))
    if len(hits) != 1:
        sys.exit("absorb_notion: %r matches %d pages in the export" % (pattern, len(hits)))
    return hits[0]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


used_ids = set()


def uid(*parts):
    base = "fol-" + "-".join(slug(p) for p in parts if p)
    i, out = 1, base
    while out in used_ids:
        i += 1
        out = "%s-%d" % (base, i)
    used_ids.add(out)
    return out


images = []


# An image generator names each file "<account>_<prompt>_<uuid>.png"; the account is the owner's, not
# the repo's to publish (owner, 2026-09-26). image_label drops that first word from a name of that
# shape, for the file written here and for the label the seed prints (check_absorb reads it the same way).
_GENERATED = re.compile(r"^[A-Za-z0-9]+_(?=.+_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.\w+$)")


def image_label(basename):
    return _GENERATED.sub("", basename)


image_names = {}                # export path -> its name here, each image its own


def image(src, from_page):
    rel = unquote(src)
    path = os.path.normpath(os.path.join(os.path.dirname(from_page), rel))
    if not os.path.isfile(path):
        sys.exit("absorb_notion: image %r (in %s) is not in the export" % (src, os.path.basename(from_page)))
    if path not in image_names:
        rel_path = os.path.join(os.path.dirname(os.path.relpath(path, ROOT)), image_label(os.path.basename(path)))
        base = slug(os.path.splitext(rel_path)[0].replace("Vampire the Masquerade - Fall of London", ""))
        # two images whose names agree as far as the slug reads them (Oliver Kensington's two portraits)
        # are two files, not one written over the other
        name, i = base, 1
        while name + ".webp" in image_names.values():
            i += 1
            name = "%s-%d" % (base, i)
        image_names[path] = name + ".webp"
        images.append((path, image_names[path]))
    return "[Image: %s](campaign/assets/gm/%s)" % (image_label(os.path.basename(path)), image_names[path])


def text_of(blocks, from_page):
    """Blocks → the GM text's Markdown, paragraph by paragraph."""
    out = []
    for b in blocks:
        k = b["kind"]
        if k == "p":
            out.append(b["text"])
        elif k == "li":
            out.append("- " + "↳ " * max(0, b["depth"] - 1) + b["text"].replace("\n", " "))
        elif k == "quote":
            out.append("\n".join("> " + ln for ln in b["text"].split("\n")))
        elif k == "img":
            out.append(image(b["src"], from_page))
        elif k == "h":
            out.append("**" + b["text"] + "**")
        elif k == "table":
            head = b["rows"][0]
            out.append("*" + " · ".join(head) + "*")
            for r in b["rows"][1:]:
                out.append("- " + " · ".join("%s: %s" % (h, c) if i else c for i, (h, c) in enumerate(zip(head, r)) if c))
        # hr: a rule between scenes; the card's paragraphs already part them
    # consecutive list items are one list: join them without the blank line
    joined = []
    for t in out:
        if joined and t.startswith("- ") and joined[-1].split("\n")[-1].startswith("- "):
            joined[-1] += "\n" + t
        else:
            joined.append(t)
    return "\n\n".join(joined)


def split_h(blocks, level):
    """[(heading or None, [blocks])] at one heading level."""
    parts = [(None, [])]
    for b in blocks:
        if b["kind"] == "h" and b["level"] == level:
            parts.append((re.sub(r"^\*+|\*+$", "", b["text"]).strip(), []))
        else:
            parts[-1][1].append(b)
    return [p for p in parts if p[0] is not None or p[1]]


def section(title, blocks, from_page, *id_parts, sub_level=None):
    sec = {"id": uid(*(id_parts or (title,))), "title": title}
    if sub_level:
        parts = split_h(blocks, sub_level)
        lead = [b for h, bl in parts if h is None for b in bl]
        sec["text"] = text_of(lead, from_page)
        sec["sections"] = [{"id": uid(*(id_parts or (title,)), h or "beat"), "title": h or "(untitled)", "text": text_of(bl, from_page)}
                           for h, bl in parts if h is not None]
    else:
        sec["text"] = text_of(blocks, from_page)
    return sec


def campaign_page():
    """The top page: its property table (System, Venue, Start Date, Sessions, Cast) and its body."""
    path = page("Vampire the Masquerade - Fall of London *.html")
    t = open(path, encoding="utf-8").read()
    props = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", t[t.index('<table class="properties"'):], re.S):
        th = re.search(r"<th[^>]*>(.*?)</th>", row, re.S)
        td = re.search(r"<td[^>]*>(.*?)</td>", row, re.S)
        if not th or not td:
            break
        name = html.unescape(re.sub(r"<[^>]+>", "", th.group(1))).strip()
        if name == "Players":
            continue  # PLAYER_NAMES
        vals = [html.unescape(re.sub(r"<[^>]+>", "", v)).strip() for v in re.split(r"<br\s*/?>|</span>|</a>", td.group(1))]
        vals = [v.strip(" ,") for v in vals if v.strip(" ,")]
        if name == "Cast":
            vals = [v.split(":", 1)[1].strip() if ":" in v else v for v in vals]  # "Player: Character - Clan"
        props.append((name, vals))
    lines = []
    for name, vals in props:
        if len(vals) > 1:
            lines.append("**%s**\n" % name + "\n".join("- " + v for v in vals))
        else:
            lines.append("**%s:** %s" % (name, vals[0] if vals else ""))
    return path, "\n\n".join(lines)


def main():
    if not os.path.isdir(EXPORT):
        sys.exit("absorb_notion: no export at %s" % EXPORT)
    overview, arc, rules, people = [], [], [], []

    # the campaign page
    top, props = campaign_page()
    overview.append({"id": uid("the-campaign"), "title": "The campaign", "text": "[NOTE] The Notion campaign page's properties (the players' names left out).\n\n" + props})

    # The Story So Far: Session Zero → overview; each other <h2> → an arc card
    story = page("Fall of London The Story So Far *.html")
    for h, bl in split_h(notion.blocks(story), 2):
        if h is None:
            if bl:
                sys.exit("absorb_notion: The Story So Far has text before its first session")
            continue
        if h == "Session Zero":
            overview.append(section(h, bl, story, "session-zero"))
            continue
        m = re.match(r"(Session \d+[a-z]?)\s*[:\-–]?\s*(.*)$", h)
        card = section(h, bl, story, h, sub_level=3)
        card["session"] = m.group(1) if m else h
        card["played"] = True
        if not card["text"] and not card["sections"]:
            card["summary"] = "No notes yet."
        arc.append(card)

    # Prep Notes and Character Maps → overview; Rules Quickreference → rules
    prep = page("Prep Notes *.html")
    overview.append(section("Prep Notes", notion.blocks(prep), prep, "prep-notes"))
    maps = page("Character Maps *.html")
    mb = [b for b in notion.blocks(maps) if b["kind"] != "img"]  # the table's portrait thumbnails: People has them
    overview.append(section("Character Maps", mb, maps, "character-maps", sub_level=2))
    rq = page("Rules Quickreference *.html")
    rb = notion.blocks(rq)
    for h, bl in split_h(rb, 2):
        rules.append(section(h or "Rules Quickreference", bl, rq, "rules", h or "quickreference", sub_level=3))

    # every row of the characters table, every column
    rows = list(csv.DictReader(open(page("Fall of London Characters *.csv"), encoding="utf-8-sig")))
    cols = [c for c in rows[0].keys() if c not in ("Name", "Picture")]
    for r in rows:
        lines = ["**%s:** %s" % (c, r[c].strip()) for c in cols if r[c].strip()]
        pics = [unquote(p.strip()) for p in r["Picture"].split(",") if p.strip()]
        csvdir = os.path.dirname(page("Fall of London Characters *.csv"))
        text = "\n".join(lines)
        if pics:
            text += "\n\n" + "\n".join(image(p, os.path.join(csvdir, "x.html")) for p in pics)
        people.append({"id": uid("person", r["Name"]), "title": r["Name"], "text": text})

    # the players' names
    blob = json.dumps([overview, arc, rules, people], ensure_ascii=False)
    for old, new in PLAYER_NAMES:
        if old not in blob:
            sys.exit("absorb_notion: PLAYER_NAMES entry %r no longer applies" % old)
    def redact(o):
        if isinstance(o, dict):
            return {k: redact(v) for k, v in o.items()}
        if isinstance(o, list):
            return [redact(v) for v in o]
        if isinstance(o, str):
            for old, new in PLAYER_NAMES:
                o = o.replace(old, new)
        return o
    overview, arc, rules, people = redact([overview, arc, rules, people])

    party = []
    order = ["alice-mockingdale", "tony-castelli", "lady-catherine-montague"]  # the book's order
    files = glob.glob(os.path.join(CAMPAIGN, "characters", "*.vtm5e-character.json"))
    for f in sorted(files, key=lambda f: (order.index(os.path.basename(f).split(".")[0]) if os.path.basename(f).split(".")[0] in order else 99, f)):
        c = json.load(open(f, encoding="utf-8"))
        party.append({"id": uid("pc", c["name"]), "templateId": c["templateId"], "name": c["name"],
                      "source": {"kind": "file", "name": os.path.basename(f)}, "character": c["values"],
                      "live": c.get("live") or {"hunger": 0}, "notes": ""})

    pack = {"kind": PACK_KIND, "version": 1, "party": party, "arc": arc, "gm": {"overview": overview, "rules": rules, "people": people}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(pack, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    # the images as WebP, 1600 px at most (the book's handouts stay legible; the portraits shrink)
    os.makedirs(IMG_DIR, exist_ok=True)
    want = {name for _p, name in images}
    for fn in os.listdir(IMG_DIR):
        if fn not in want:
            os.remove(os.path.join(IMG_DIR, fn))
    for path, name in images:
        dst = os.path.join(IMG_DIR, name)
        if not os.path.isfile(dst) or os.path.getmtime(dst) < os.path.getmtime(path):
            subprocess.run(["magick", path + "[0]", "-strip", "-resize", "1600x1600>", "-quality", "84",
                            "-define", "webp:method=6", dst], check=True)
    print("absorb_notion: party %d · overview %d · arc %d sessions (%d beats) · rules %d · people %d · %d images → %s"
          % (len(party), len(overview), len(arc), sum(len(c.get("sections") or []) for c in arc), len(rules), len(people),
             len(want), os.path.relpath(OUT, REPO)))


if __name__ == "__main__":
    main()
