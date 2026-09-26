#!/usr/bin/env python3
"""
check_pregens.py — proves each herald's character file (campaign/characters/*.json) says what
the book prints, in both directions. Shares no code with convert_pregens.py.

It reads the appendix straight out of the corpus file (the .ttrpg, not the VTT's data), finds
each character's block of text by its "Your name is …" line, and then:

  * every value in the file is printed in that block, on the right line, with the right number
    (an Attribute or Skill as "Name N", a specialty in brackets, a Discipline as "Name N (powers)",
    Clan / Sire / Ambition / Predator / Generation / Humanity / Blood Potency / Bane / Convictions,
    birth and Embrace years)
  * every rated trait the block prints is in the file with that rating, and no Skill the block
    does not print is rated in the file
  * nothing the Storyteller keeps (ACTUAL AMBITION, SUGGESTED NEW TOUCHSTONE) is in the file

    python3 campaign/source/check_pregens.py [corpus .ttrpg]
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN = os.path.dirname(HERE)
CORPUS = os.path.expanduser("~/Sortilege/Titterpig/DSL/titterpig-dsl-vtm5e/0.5/vtm5e-0.5-fall-of-london-playable-characters.ttrpg")
FIRST = {"Alice Mockingdale": "Alice", "Tony Castelli": "Tony", "Lady Catherine Montague": "Catherine"}
SKILLS = ("Athletics Brawl Craft Drive Firearms Melee Larceny Stealth Survival|Animal Ken|Etiquette Insight "
          "Intimidation Leadership Performance Persuasion Streetwise Subterfuge Academics Awareness Finance "
          "Investigation Medicine Occult Politics Science Technology")
SKILLS = [s for grp in SKILLS.split("|") for s in ([grp] if " " in grp and grp == "Animal Ken" else grp.split())]


def corpus_text(path):
    raw = open(path, encoding="utf-8").read()
    texts = re.findall(r'TEXT "((?:[^"\\]|\\.)*)"', raw)
    return "\n\n".join(json.loads('"%s"' % t) for t in texts)


def block_for(text, first):
    at = text.find("PLAYER INFORMATION: Your name is %s" % first)
    if at == -1:
        return None
    start = text.rfind("\nCLAN:", 0, at)
    start = 0 if start == -1 and text.startswith("CLAN:") else start
    end = text.find("\nCLAN:", at)
    return text[start:end if end != -1 else len(text)]


def line(block, label):
    b = re.sub(r"\s*\n\s*\n\s*", " ", block)  # paragraph breaks inside a label or value
    m = re.search(r"%s: (.*?)(?= [A-Z][A-Z ]{3,}: |$)" % re.escape(label), b)
    return m.group(1).strip() if m else None


def main():
    corpus = sys.argv[1] if len(sys.argv) > 1 else CORPUS
    text = corpus_text(corpus)
    files = sorted(glob.glob(os.path.join(CAMPAIGN, "characters", "*.vtm5e-character.json")))
    fails, checks = [], 0

    def ok(cond, who, what):
        nonlocal checks
        checks += 1
        if not cond:
            fails.append("%s: %s" % (who, what))

    seen = set()
    for path in files:
        c = json.load(open(path, encoding="utf-8"))
        v, who = c["values"], c["name"]
        if who not in FIRST:
            fails.append("%s: not a pregen this chronicle plays" % who)
            continue
        seen.add(who)
        blk = block_for(text, FIRST[who])
        if not blk:
            fails.append("%s: no block in the corpus" % who)
            continue
        for key, label in (("Clan", "CLAN"), ("Sire", "SIRE"), ("Ambition", "AMBITION"), ("Predator", "PREDATOR TYPE")):
            ok(v.get(key) == line(blk, label), who, "%s %r ≠ the book's %s %r" % (key, v.get(key), label, line(blk, label)))
        ok(str(v.get("Generation")) + "th" == line(blk, "GENERATION"), who, "Generation %r vs %r" % (v.get("Generation"), line(blk, "GENERATION")))
        for key, label in (("Humanity", "HUMANITY"), ("Blood Potency", "BLOOD POTENCY")):
            ok(str(v.get(key)) == line(blk, label), who, "%s %r vs %r" % (key, v.get(key), line(blk, label)))
        bane = line(blk, "BANE")
        ok((v.get("Clan Bane") or None) == bane, who, "Clan Bane %r vs %r" % (v.get("Clan Bane"), bane))
        ok(v.get("Touchstones & Convictions") == [line(blk, "CONVICTIONS")], who, "Convictions differ")
        emb = line(blk, "EMBRACED")
        ok(emb == "%s (Born %s)" % (v.get("Date of death"), v.get("Date of birth")), who, "EMBRACED %r vs death %r / birth %r" % (emb, v.get("Date of death"), v.get("Date of birth")))
        # Attributes and Health/Willpower: both directions
        for label in ("ATTRIBUTES", "SECONDARY ATTRIBUTES"):
            printed = dict((n, int(r)) for n, r in re.findall(r"([A-Z][a-z]+) (\d)", line(blk, label) or ""))
            ok(len(printed) == (9 if label == "ATTRIBUTES" else 2), who, "%s: read %d traits" % (label, len(printed)))
            for n, r in printed.items():
                ok(v.get(n) == r, who, "%s %s: file %r, book %d" % (label, n, v.get(n), r))
        # Skills: every printed one, and nothing else rated
        sk = line(blk, "SKILLS") or ""
        printed = {}
        for n, spec, r in re.findall(r"([A-Z][a-z]+(?: Ken)?)\s*(?:\(([^)]*)\))?\s+(\d)", sk):
            printed[n] = (int(r), spec or None)
        for n, (r, spec) in printed.items():
            ok(v.get(n) == r, who, "Skill %s: file %r, book %d" % (n, v.get(n), r))
            fs = [s["Specialty"] for s in v.get("Specialties") or [] if s["Skill"] == n]
            ok(fs == ([spec] if spec else []), who, "Skill %s specialty: file %r, book %r" % (n, fs, spec))
        for n in SKILLS:
            if n not in printed:
                ok(not v.get(n), who, "Skill %s rated %r in the file, not printed in the book" % (n, v.get(n)))
        # Disciplines
        dl = line(blk, "DISCIPLINES") or ""
        printed = [(n, int(r), [p.strip() for p in ps.split(",")]) for n, r, ps in re.findall(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?) (\d) \(([^)]*)\)", dl)]
        got = [(d["Discipline"], d["Dots"], d["Powers"]) for d in v.get("Disciplines") or []]
        ok(got == printed, who, "Disciplines: file %r, book %r" % (got, printed))
        # the Storyteller's lines are not on the sheet
        blob = json.dumps(v, ensure_ascii=False)
        for label in ("ACTUAL AMBITION", "SUGGESTED NEW TOUCHSTONE", "SUGGESTED NEW"):
            val = line(blk, label)
            if val:
                ok(val[:40] not in blob, who, "%s is on the sheet" % label)
    for who in FIRST:
        ok(who in seen, who, "no character file")
    if fails:
        print("check_pregens: FAILED (%d checks)" % checks)
        for f in fails:
            print("  " + f)
        return 1
    print("check_pregens: OK — %d characters, %d checks against %s" % (len(seen), checks, os.path.basename(corpus)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
