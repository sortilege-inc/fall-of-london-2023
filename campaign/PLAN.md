# Fall of London × sortilege-vtt-vtm5e — plan and decision log

A **Vampire: The Masquerade 5th Edition** chronicle, 2023–2024, played through Renegade's
*The Fall of London* (in the corpus as `fall-of-london`): four of Mithras' heralds wake beneath
London on 19 March 2012. Built as an **instance** of `sortilege-vtt-vtm5e`, the second after
[`blood-and-other-drugs`](../../../2025-2026%20Blood%20%26%20Other%20Drugs/blood-and-other-drugs), whose
shape it follows. The process is `~/Sortilege/VTT/INSTANCES.md`.

Status words: **PROPOSED** (awaiting the owner), **(owner)** decided, **landed** built and proven.

## What is on disk (read 2026-09-25)

| Input | State |
|---|---|
| `sortilege-inc/fall-of-london-2023` | cloned 2026-09-25, **empty**, **PUBLIC**; identity Jordan Peacock <jordan@sortilege.online> and `merge.ours.driver` set |
| The owner's Notion export | copied to `../notion-export/` (**beside** the repo, never in it). The campaign page; *The Story So Far* (Session Zero–20, ~23k words, the Storyteller's session notes; Session 20 has only its heading); *Fall of London Characters* (50 rows, CSV + a page each, 29 pictures); *Character Maps*; *Prep Notes*; *Rules Quickreference* |
| The book | *The Fall of London* is on the shelf (11 files). Its pregens — Alice Mockingdale, Tony Castelli, Lady Catherine Montague, Doctor Henry Banerjee (pp. 241–247) — are **sidebar text**, not sheet records |
| Records | **No Foundry world.** Matthias Darkwood (Hecata) is not in the book; his sheet is to come from the owner |

## Owner decisions (2026-09-25)

**O1 — Build local, deploy on the owner's go.** Nothing is pushed until the owner has seen it and
says go; then Pages from `main` + a `fall-of-london` Worker, as B&OD. The first push publishes
upstream's `data/` (the books) — the repo is public.

**O2 — Pregens + Matthias's file.** Alice, Tony and Catherine are the book's pregens; Matthias from
a file the owner supplies. NPCs the book prints point at the book.

**O3 — The Chronicle is written chapters, B&OD-style**, from *The Story So Far* (the authority),
inventing nothing; a pilot first. Voice proposed: gothic London noir (owner may name another).

**O4 — The look:** B&OD's approach with a more ivory ground, after the *Laws of the Night* cover.

**O5 — "GM notes should all be available in the GM section."** Every Notion GM page goes into the
GM tabs through the seed (PLAYBOOK §4b.2).

## Milestones

| # | What | Proof |
|---|---|---|
| **M1** | **The fork.** `main` based on `upstream/main` (9bd4598) — the repo was empty, so no move and no unrelated-histories merge; the instance-owned root files; `merge=ours`; launch `fall` 8744 / `fall-worker` 8797 | **landed** `75fa2a2`. Boundary **proven by making it fail** in a throwaway clone: a fake upstream commit changing `title:` in `engine/config.js` and appending to `index.html` — without the driver `CONFLICT (content): Merge conflict in engine/config.js`; with it, merged clean, title stayed *Fall of London*, `index.html` took the change |
| **M3a** | **The look and the site.** `campaign/site/campaign.css`, `site.js`; Home, The Heralds, Dramatis Personae, The Chronicle | **landed** `eb46a00`. Browser (8744): site, a person page, `/gm/` and its veil all ivory; 0 console errors |
| **M3b** | **People** from the owner's table: `campaign/source/convert_people.py` | **landed** `eb46a00`: 50 rows → 8 heralds and party · 41 dramatis personae · 1 not player-visible (*[Stub] Puttanesca*); 27 portraits as WebP; a rerun byte-identical (md5 of the pages before/after equal) |
| **M5a** | **The GM's Notion pages in the GM tabs**: `absorb_notion.py` → `campaign/pack/seed.json`, `check_absorb.py` | **landed** `eb46a00`: Overview 4 (the campaign, Session Zero, Prep Notes, Character Maps), Rulings 1, Scenes 23 sessions / 10 beats (all played), People 50, 33 images. check_absorb: *The Story So Far* 23,335 words, Prep Notes 797, Character Maps 616, Rules Quickreference 483 — all OK; characters 50 rows / 297 cells OK. **Proven by planting three faults** (a word dropped from Session 3, Alice's clan changed, a player's name added to Prep Notes): all three named, exit 1. In the browser, after a cleared store: `gm` overview 4 / rules 1 / people 50, arc 23, `seeded` 97; the panes draw them |
| **M3c** | **The Chronicle**: a pilot for the owner, then the rest | **pilot PROPOSED**: chapters 1 *Awakenings* and 2 *Debriefing* (Sessions 1–2, one night; Session 1 alone is ~300 words of notes), written only from the notes — no dice, no rules names, no player names; Doctor Banerjee is not explained away in ch. 2, since the notes do not say where he went |
| **M2** | **The heralds' sheets**: the pregens' sidebar statistics → a DSL layer (`campaign/dsl/`), checked field by field against the book's text; Matthias from the owner's file | waits on Matthias's file for completeness; the three pregens can go first |
| **M6** | Sessions through the Worker | — |
| **M7** | Deploy (O1) | the owner's go |

## Open

* **Matthias Darkwood's sheet** — the owner's file (O2).
* **Session 20** has a heading and no notes; the Notion session list ends *Finale (async)*.
* **Session 6b** (*How Alice got the Ring*) is one line.

## Decision log

| When | Kind | Decision | Why |
|---|---|---|---|
| 2026-09-25 | autonomous, method | `main` **based on upstream's history** rather than B&OD's move + `--allow-unrelated-histories` | The repo was empty: nothing to move; a shared history makes every later pull an ordinary merge |
| 2026-09-25 | autonomous, config | `defaultCampaign.modules` kept at upstream's `['chronicle']` (B&OD had `[]`); `defaultSlots` Overview · Scenes · People | The Chronicle panel is the system's scene tracker; the GM opens on the material the owner asked to have there (O5) |
| 2026-09-25 | autonomous, look | The VTT's dark family (`--night*`, `--bone*`) **re-pointed** at ivory and ink in `campaign.css` rather than restyling selectors; Cinzel for display; hairline marble veins from a seeded script; the cover's red ring drawn as SVG | One file, no upstream edit; every page (site, table, player, veil) takes it |
| 2026-09-25 | autonomous, **privacy** | **The Notion export stays outside the repo** (`../notion-export/`); converters read it from there | It holds the Storyteller's prep and the players' names, and the repo is public |
| 2026-09-25 | autonomous, **privacy** | **Players' names are not in the seed**: the campaign page's *Players* property is dropped, *Cast* keeps the characters without the player, one mention in Prep Notes becomes *[a player]* (`PLAYER_NAMES`, which fails if stale). The check counts a leaked name as an extra word | The seed is served publicly with the site. **For the owner:** say if the GM tabs should carry them |
| 2026-09-25 | autonomous, scope | Dramatis Personae holds exactly the table's **player-visible** rows, each page the table's own values (Titles, Clan, Affiliations, Stage of Life, Deceased?, Short Note) — nothing written about anyone. Circles are Character Maps' own tables, first that lists a person; the three in none are placed by affiliation (*Camarilla* → the Court) or under *Others met* | The table is the owner's record of what the players may see |
| 2026-09-25 | autonomous, scope | The Heralds: the four PCs, then *Those who run with them* (the table's other **Party** rows: Oliver Kensington, Ferhat, Claire, Adisa). Doctor Henry Banerjee stays with the Cult, as the table files him | His player left after Session 1 (the notes, Session 2) |
| 2026-09-25 | autonomous, **for the owner** | **Seven portraits look like published art** (Queen Anne, Regina Blake, Richard de Worde, Sri Sansa, Valerius, Edward Bainbridge; Pater Thomas's file is named *From_Trails_of_Ash_and_Bone*). Used as the owner's table uses them | The site already serves the books' text; say if they should come off the public pages |
| 2026-09-25 | autonomous, method | The seed's images (the book's handouts in the notes — the *Shelter Here* map, the psychic's flyer, the bunker plan, Pater Thomas's letter; a core-page scan in Rules; every picture in the table) are WebP ≤1600 px in `campaign/assets/gm/`, linked where they stood | The GM text draws links, not images; the handouts stay legible |
