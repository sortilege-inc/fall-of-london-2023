# campaign/docs — the chronicle's published prose

Markdown, one file per page. `bash campaign/build/build.sh` turns it into
`campaign/data/docs.js`, which the site's campaign tabs render (`campaign/site/site.js`). The
build fails, naming the file, on a bad key, a missing file, an unknown entity, a broken
`[[link]]` or a page in no section.

A page may open with front matter: `key: value` lines between `---` fences. Paths are relative
to `campaign/`. The file name (without `.md`) is the page's slug, unique across every section,
and sets the order within its section.

| Where | Site tab | Front matter (**required**) | The body |
|---|---|---|---|
| `home.md` | Home | — | The front page, above the cards into every section: the table's Session Zero tenets and lines & veils, verbatim. |
| `heralds/*.md` | The Heralds | **name**, **group**, epithet, clan, portrait, entity, deceased | The four heralds, then the rest of the party. **Generated** by `campaign/source/convert_people.py` from the owner's Notion table. |
| `dramatis-personae/*.md` | Dramatis Personae | **name**, **circle**, epithet, clan, portrait, entity, first, deceased | Everyone else the table marks player-visible, grouped by the owner's Character Maps. **Generated**, as above. |
| `chronicle/*.md` | The Chronicle | **title**, part, date, played | One session (or a part of one) as a chapter, written from the owner's session notes (*The Story So Far*), which are the authority. Prose only: no dice, no named rules, no player names. |

The generated pages are rewritten on every run of the converter, **except** what is below the
line `<!-- written by hand below this line; convert_people.py keeps it -->` — write there.

**Everything in `docs/` is published with the site**, so it holds only what the table knows.
The Storyteller's own material — prep, threads, secrets — goes in the GM tabs on `/gm/`, saved in
the pack, never here. A `.md` anywhere not listed above fails the build.

Link any page to any other with `[[slug]]` or `[[slug|the words shown]]`.
