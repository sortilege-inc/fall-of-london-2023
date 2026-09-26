#!/usr/bin/env python3
"""
convert_pregens.py — the book's pregenerated heralds → the VTT's character files.

*The Fall of London* prints its five player characters (Appendix III, pp. 241–247) as sidebar
text — `CLAN: …`, `ATTRIBUTES: Strength 2, …`, `DISCIPLINES: Auspex 1 (Sense the Unseen), …` —
not as sheet records. This reads that text from the VTT's own `data/fall-of-london.js` (the
corpus, verbatim) and writes, for the three heralds played in this chronicle, a character file
the Coterie loads (`sortilege-vtt-character`, the ACTOR "Kindred" of the BASE):

    campaign/characters/alice-mockingdale.vtm5e-character.json
    campaign/characters/tony-castelli.vtm5e-character.json
    campaign/characters/lady-catherine-montague.vtm5e-character.json

The sidebars are read in page order and split at each `CLAN:`; a block belongs to the character
its `PLAYER INFORMATION: Your name is …` names. That, and not the DEF a sidebar sits under, is
the key, because the extraction files several sidebars under the neighbouring character (Tommy
Smith's statistics are inside the Tony Castelli DEF; Doctor Banerjee's inside Lady Catherine's)
— a corpus defect, reported to its TODO, never corrected here.

Every value is the book's. What the sheet has a place for is filled from the line that prints it:
Clan, Sire, Ambition, Predator (PREDATOR TYPE), Generation, Humanity, Blood Potency, the nine
Attributes, Health and Willpower (SECONDARY ATTRIBUTES), each Skill and its specialty in brackets,
each Discipline with its dots and the powers in brackets, Clan Bane (BANE, where printed),
Touchstones & Convictions (CONVICTIONS), Date of birth and Date of death (EMBRACED: 1867 (Born
1847) → born 1847, died 1867). ACTUAL AMBITION and SUGGESTED NEW TOUCHSTONE are the Storyteller's
(the book: "some sections are intentionally left blank as only the Storyteller knows") and stay
in the book. Chronicle is this chronicle's name.

A clan, a Discipline and each power are checked to be names the books print (the VTT's
data/records.js and the BASE's Discipline ENUM); a name that is not fails the run.

    python3 campaign/source/convert_pregens.py
"""
import json
import os
import re
import sys

CAMPAIGN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(CAMPAIGN)
BOOK = os.path.join(REPO, "data", "fall-of-london.js")
RECORDS = os.path.join(REPO, "data", "records.js")
OUT = os.path.join(CAMPAIGN, "characters")
FILE = "playable-characters"
CHRONICLE = "Fall of London"
TEMPLATE = "#vtm5Kindred000000001"
# the player character played, keyed by the name the book gives them in PLAYER INFORMATION
PLAYED = {"Alice": "Alice Mockingdale", "Tony": "Tony Castelli", "Catherine": "Lady Catherine Montague"}
ATTRIBUTES = ["Strength", "Dexterity", "Stamina", "Charisma", "Manipulation", "Composure", "Intelligence", "Wits", "Resolve"]
SKILLS = ["Athletics", "Brawl", "Craft", "Drive", "Firearms", "Melee", "Larceny", "Stealth", "Survival",
          "Animal Ken", "Etiquette", "Insight", "Intimidation", "Leadership", "Performance", "Persuasion",
          "Streetwise", "Subterfuge", "Academics", "Awareness", "Finance", "Investigation", "Medicine",
          "Occult", "Politics", "Science", "Technology"]
LABELS = ["CLAN", "SIRE", "EMBRACED", "AMBITION", "ACTUAL AMBITION", "CONVICTIONS", "SUGGESTED NEW TOUCHSTONE",
          "HUMANITY", "GENERATION", "BLOOD POTENCY", "ATTRIBUTES", "SECONDARY ATTRIBUTES", "SKILLS",
          "DISCIPLINES", "CEREMONY", "PREDATOR TYPE", "BANE", "PLAYER INFORMATION"]


def fail(msg):
    sys.exit("convert_pregens: " + msg)


def book_entities():
    t = open(BOOK, encoding="utf-8").read()
    m = re.search(r"var d=(\{.*?\});var T=window\.VTM5E", t, re.S)
    d = json.loads(m.group(1))
    ch = next(c for c in d["book"]["chapters"] if FILE in c["file"])
    return d["entities"], ch["roots"]


def sidebar_text():
    """Every sidebar of the appendix, in page (root) order, as one text."""
    ents, roots = book_entities()
    parts = []
    for r in roots:
        for g in ents[r].get("guidance") or []:
            parts.append(g["text"])
    return "\n\n".join(parts)


def blocks(text):
    """The text split at each `CLAN:` that starts a line; each block's fields by label."""
    out = []
    starts = [m.start() for m in re.finditer(r"(?m)^CLAN: ", text)]
    for i, s in enumerate(starts):
        chunk = text[s:starts[i + 1] if i + 1 < len(starts) else len(text)]
        # a label may be broken across a paragraph ("SUGGESTED NEW\n\nTOUCHSTONE:")
        chunk = re.sub(r"SUGGESTED NEW\s*\n\s*\n\s*TOUCHSTONE:", "SUGGESTED NEW TOUCHSTONE:", chunk)
        chunk = re.sub(r"SECONDARY ATTRIBUTES:\s*\n\s*\n\s*", "SECONDARY ATTRIBUTES: ", chunk)
        fields = {}
        pat = re.compile(r"(?m)^(%s): " % "|".join(re.escape(l) for l in sorted(LABELS, key=len, reverse=True)))
        ms = list(pat.finditer(chunk))
        for j, m in enumerate(ms):
            end = ms[j + 1].start() if j + 1 < len(ms) else len(chunk)
            val = chunk[m.end():end].strip()
            if m.group(1) != "PLAYER INFORMATION":
                val = val.split("\n\n")[0].strip()  # a field is one paragraph
            fields[m.group(1)] = val
        who = re.match(r"Your name is (\w+)", fields.get("PLAYER INFORMATION", ""))
        out.append((who.group(1) if who else None, fields))
    return out


def split_top(s):
    """"A 1 (x, y), B 2" → ["A 1 (x, y)", "B 2"]: commas outside brackets."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch in ",;" and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [x.rstrip(".") for x in out if x]


def rated(s):
    """"Occult (Witchcraft) 4" / "Persuasion(Seduction) 3" / "Auspex 1 (Sense the Unseen)" → (name, n, bracket)."""
    m = re.match(r"^(.+?)\s*(?:\(([^)]*)\))?\s+(\d+)\s*(?:\(([^)]*)\))?$", s.strip())
    if not m:
        fail("cannot read %r as a name and a rating" % s)
    return m.group(1).strip(), int(m.group(3)), (m.group(2) or m.group(4))


def known_names():
    t = open(RECORDS, encoding="utf-8").read()
    i = t.index("T.records=") + len("T.records=")
    recs, _ = json.JSONDecoder().raw_decode(t[i:])
    powers = {(r.get("discipline"), r["name"]) for r in recs if r["kind"] in ("power", "ritual")}
    base = open(os.path.join(REPO, "data", "base.js"), encoding="utf-8").read()
    return powers, base


def character(first, f, powers, base):
    name = PLAYED[first]
    v = {"Name": name, "Chronicle": CHRONICLE}
    v["Clan"] = f["CLAN"]
    v["Sire"] = f["SIRE"]
    v["Ambition"] = f["AMBITION"]
    v["Predator"] = f["PREDATOR TYPE"]
    v["Generation"] = int(re.match(r"(\d+)", f["GENERATION"]).group(1))
    v["Humanity"] = int(f["HUMANITY"])
    v["Blood Potency"] = int(f["BLOOD POTENCY"])
    for part in split_top(f["ATTRIBUTES"]):
        n, r, _b = rated(part)
        if n not in ATTRIBUTES:
            fail("%s: %r is not an Attribute" % (name, n))
        v[n] = r
    for part in split_top(f["SECONDARY ATTRIBUTES"]):
        n, r, _b = rated(part)
        v[n] = r
    for s in SKILLS:
        v[s] = 0
    specs = []
    for part in split_top(f["SKILLS"]):
        n, r, b = rated(part)
        if n not in SKILLS:
            fail("%s: %r is not a Skill" % (name, n))
        v[n] = r
        if b:
            specs.append({"Skill": n, "Specialty": b})
    v["Specialties"] = specs
    discs = []
    for part in split_top(f["DISCIPLINES"]):
        n, r, b = rated(part)
        if '"%s"' % n not in base:
            fail("%s: %r is not a Discipline the BASE names" % (name, n))
        ps = [p.strip() for p in (b or "").split(",") if p.strip()]
        for p in ps:
            if (n, p) not in powers:
                fail("%s: %s power %r is in no book" % (name, n, p))
        discs.append({"Discipline": n, "Dots": r, "Powers": ps})
    v["Disciplines"] = discs
    if "BANE" in f:
        v["Clan Bane"] = f["BANE"]
    v["Touchstones & Convictions"] = [f["CONVICTIONS"]]
    m = re.match(r"(\d{4})\s*\(Born (\d{4})\)", f["EMBRACED"])
    if not m:
        fail("%s: EMBRACED %r is not 'year (Born year)'" % (name, f["EMBRACED"]))
    v["Date of death"], v["Date of birth"] = m.group(1), m.group(2)
    return {"kind": "sortilege-vtt-character", "v": 2, "system": "vtm5e", "templateId": TEMPLATE,
            "name": name, "values": v, "live": {"hunger": 0},
            "source": "The Fall of London, Appendix III: Playable Characters (corpus fall-of-london, %s)" % FILE}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    powers, base = known_names()
    found = {}
    for first, f in blocks(sidebar_text()):
        if first in PLAYED:
            if first in found:
                fail("two sidebars name %s" % first)
            found[first] = character(first, f, powers, base)
    missing = [p for p in PLAYED if p not in found]
    if missing:
        fail("no sidebar for %s" % missing)
    os.makedirs(OUT, exist_ok=True)
    for first, c in found.items():
        path = os.path.join(OUT, slug(c["name"]) + ".vtm5e-character.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(c, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        v = c["values"]
        print("convert_pregens: %-24s %s · %s · gen %s · %d skills · %s" % (
            c["name"], v["Clan"], v["Predator"], v["Generation"], sum(1 for s in SKILLS if v[s]),
            ", ".join("%s %d" % (d["Discipline"], d["Dots"]) for d in v["Disciplines"])))


if __name__ == "__main__":
    main()
