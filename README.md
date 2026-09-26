# Fall of London

A **Vampire: The Masquerade 5th Edition** chronicle (2023–2024), played through Renegade's
*The Fall of London*: four of Mithras' heralds wake beneath the city in March 2012 into a London
where their god is said to be dead, Queen Anne holds the praxis, and Operation Antigen is closing
in. It is served as an **instance** of
[sortilege-vtt-vtm5e](https://github.com/sortilege-inc/sortilege-vtt-vtm5e).

The VTT owns the root: the site at `/`, the Storyteller's table at `/gm/`, the engine, the
VtM5e system module, and the books generated from the Titterpig corpus. The campaign owns
`campaign/`.

- `campaign/PLAN.md` — the decisions, the milestones, and their proof.
- The process: `~/Sortilege/VTT/INSTANCES.md`; the sibling instance this one follows is
  [blood-and-other-drugs](https://github.com/sortilege-inc/blood-and-other-drugs).

## The fork

`upstream` is the VTT. Engine and system updates arrive by

```bash
git fetch upstream && git merge upstream/main
```

Upstream-owned files are never edited here — anything every VtM campaign would want is built
upstream and pulled. The instance's own root files (`engine/config.js`, `worker/wrangler.jsonc`,
`README.md`, `CNAME`, `.gitignore`, `.claude/launch.json`, `.gitattributes`) are marked
`merge=ours`, so a pull keeps this repo's copy. That needs a driver git does not store; run once
per clone:

```bash
git config merge.ours.driver true
```

Because `merge=ours` keeps the instance's *whole* `engine/config.js`, a key upstream adds there
never arrives on its own: after each pull, read
`git diff <last pulled>..upstream/main -- engine/config.js` and carry what applies.

## Local

Launch entries `fall` (site, 8744) and `fall-worker` (sessions, 8797).

## Rights

*Vampire: The Masquerade* and *The Fall of London* are © Paradox Interactive / World of Darkness
and Renegade Game Studios. This is an unofficial play aid for the owner's table, not a
redistribution of the books.
