// campaign/site/site.js — Fall of London's own tabs on the VTT's site, ahead of the books: Home,
// The Heralds, Dramatis Personae, The Chronicle. Loaded at the `site` stage (engine/instance.js),
// after the system's tabs and before engine/site.js renders, so the chronicle's Home is the tab
// the site opens on. The prose is campaign/data/docs.js, built from campaign/docs/ by
// campaign/build/build_docs.py; the people pages come from the owner's Notion table
// (campaign/source/convert_people.py).
//
// Everything here is public, so it holds only what the table knows: a person is listed once the
// owner's table marks them player-visible. What they really are is the Storyteller's, in the GM
// tabs on /gm/ — and no stat block is drawn here.
(function () {
  const { el } = window.VttRender;
  const CFG = window.VttConfig || {};
  const DOCS = window.FallDocs || {};
  const Site = () => window.VttSite;

  // the band: the brand opens the chronicle, not the shelf
  document.querySelectorAll('a.brand').forEach((a) => a.setAttribute('href', '#home'));
  document.querySelectorAll('.brand-sub').forEach((n) => (n.textContent = 'a Vampire: The Masquerade chronicle · London, 2012'));

  const list = (k) => DOCS[k] || [];
  const bySlug = (k, slug) => list(k).find((p) => p.slug === slug) || null;

  // A doc's HTML, its [[links]] routed through the site's own tabs.
  function prose(html, cls) {
    const box = el('div', { class: 'prose fall-prose' + (cls ? ' ' + cls : '') });
    box.innerHTML = html || '';
    box.querySelectorAll('a.doc-link').forEach((a) => {
      const tab = a.getAttribute('data-tab');
      if (tab) a.setAttribute('href', Site().href(tab, [a.getAttribute('data-slug')]));
    });
    return box;
  }
  const empty = (what) => el('div', { class: 'empty' }, ['Nothing ' + what + ' yet.']);
  const crumbs = (ctx, tab, title, name) => el('div', { class: 'crumbs' }, [el('a', { href: ctx.href(tab, []) }, [title]), ' › ', name]);
  const portrait = (src, name) => (src ? el('img', { class: 'fall-portrait', src, alt: name || '' }) : null);
  const meta = (bits) => el('div', { class: 'entity-sub' }, [bits.filter(Boolean).join(' · ')]);
  // groups in the order their first page appears (the file names set the order)
  function groups(pages, key) {
    const out = [];
    pages.forEach((p) => {
      const g = p[key] || '';
      let grp = out.find((x) => x.name === g);
      if (!grp) out.push((grp = { name: g, pages: [] }));
      grp.pages.push(p);
    });
    return out;
  }
  const page = (container) => { const p = el('div', { class: 'page fall-page' }); container.appendChild(p); return p; };
  const reader = (kids, cls) => el('div', { class: 'site-reader solo' + (cls ? ' ' + cls : '') }, kids);

  // the cover's brushstroke: an open red ring, drawn rather than fetched
  function ring() {
    const NS = 'http://www.w3.org/2000/svg';
    const s = document.createElementNS(NS, 'svg');
    s.setAttribute('viewBox', '0 0 200 200'); s.setAttribute('class', 'fall-ring'); s.setAttribute('aria-hidden', 'true');
    [[9, .9, 'M 30 150 A 84 84 0 1 1 172 128'], [4, .55, 'M 40 160 A 80 80 0 1 1 178 112'], [2, .45, 'M 22 132 A 88 88 0 0 1 150 20']].forEach(([w, o, d]) => {
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', d); p.setAttribute('fill', 'none'); p.setAttribute('stroke', 'var(--blood-2)');
      p.setAttribute('stroke-width', w); p.setAttribute('stroke-opacity', o); p.setAttribute('stroke-linecap', 'round');
      s.appendChild(p);
    });
    return s;
  }

  // ── Home ────────────────────────────────────────────────────────────
  const SECTIONS = [
    ['heralds', 'The Heralds', (n) => n('heralds', 'of them', 'of them')],
    ['people', 'Dramatis Personae', (n) => n('people', 'person', 'people')],
    ['chronicle', 'The Chronicle', (n) => n('chronicle', 'chapter', 'chapters')],
  ];
  function renderHome(container, path, ctx) {
    const p = page(container);
    p.appendChild(el('div', { class: 'hero fall-hero' }, [
      el('div', { class: 'fall-title-wrap' }, [ring(), el('div', { class: 'fall-title' }, [el('small', {}, ['Vampire: The Masquerade']), CFG.title || 'The chronicle'])]),
      el('p', { class: 'hero-sub' }, ['London, March 2012. Mithras is said to be dead, and his heralds have woken.']),
    ]));
    if (DOCS.home && DOCS.home.html) {
      const body = prose(DOCS.home.html);
      const h1 = body.querySelector('h1');
      if (h1 && h1.textContent.trim() === (CFG.title || '').trim()) h1.remove();
      if (body.textContent.trim()) p.appendChild(reader([body], 'fall-home'));
    }
    const n = (k, one, many) => { const c = list(k).length; return c ? c + ' ' + (c === 1 ? one : many) : 'nothing yet'; };
    p.appendChild(el('div', { class: 'shelf fall-shelf' }, SECTIONS.map(([tab, title, sub]) =>
      el('a', { class: 'shelf-book fall-card', href: ctx.href(tab, []) }, [el('div', { class: 'shelf-title' }, [title]), el('div', { class: 'shelf-meta' }, [sub(n)])]))));
  }

  // ── The Chronicle ───────────────────────────────────────────────────
  function renderChronicle(container, path, ctx) {
    const p = page(container);
    const all = list('chronicle');
    const ch = path[0] && bySlug('chronicle', path[0]);
    if (ch) {
      const i = all.indexOf(ch);
      p.appendChild(crumbs(ctx, 'chronicle', 'The Chronicle', ch.title));
      p.appendChild(reader([
        ch.part ? el('div', { class: 'entity-sub fall-part' }, [ch.part]) : null,
        el('h2', { class: 'chapter-h' }, [ch.title]),
        meta([ch.date, ch.played ? 'played ' + ch.played : null]),
        prose(ch.html, 'fall-chapter'),
        el('div', { class: 'fall-paging' }, [
          i > 0 ? el('a', { href: ctx.href('chronicle', [all[i - 1].slug]) }, ['‹ ' + all[i - 1].title]) : el('span'),
          i < all.length - 1 ? el('a', { href: ctx.href('chronicle', [all[i + 1].slug]) }, [all[i + 1].title + ' ›']) : el('span'),
        ]),
      ]));
      return;
    }
    p.appendChild(el('h2', { class: 'chapter-h' }, ['The Chronicle']));
    if (!all.length) return p.appendChild(empty('told'));
    let n = 1;
    groups(all, 'part').forEach((g) => {
      if (g.name) p.appendChild(el('h4', { class: 'fall-group' }, [g.name]));
      p.appendChild(el('ol', { class: 'fall-toc', start: String(n) }, g.pages.map((x) => (n++, el('li', {}, [
        el('a', { href: ctx.href('chronicle', [x.slug]) }, [x.title]),
        [x.played, x.date].filter(Boolean).length ? el('span', { class: 'muted small' }, [' · ' + [x.played, x.date].filter(Boolean).join(' · ')]) : null,
      ])))));
    });
  }

  // ── people: the Heralds and the Dramatis Personae ──────────────────
  function personCard(ctx, tab, x) {
    return el('a', { class: 'card fall-person' + (x.deceased ? ' dead' : ''), href: ctx.href(tab, [x.slug]) }, [
      x.portrait ? el('img', { class: 'fall-thumb', src: x.portrait, alt: '' }) : el('span', { class: 'fall-thumb none' }),
      el('div', {}, [
        el('div', { class: 'card-name' }, [x.name]),
        el('div', { class: 'card-text' }, [[x.epithet, x.clan].filter(Boolean).join(' · ')]),
        x.deceased ? el('div', { class: 'fall-dead' }, ['Deceased']) : null,
      ]),
    ]);
  }
  function personPage(container, ctx, tab, title, x, bits) {
    const p = page(container);
    p.appendChild(crumbs(ctx, tab, title, x.name));
    p.appendChild(reader([portrait(x.portrait, x.name), el('h2', { class: 'chapter-h' }, [x.name]),
      meta(bits), x.deceased ? el('div', { class: 'fall-dead' }, ['Deceased']) : null, prose(x.html)], 'fall-person-page'));
  }
  function peopleTab(tab, title, key, lede) {
    return function (container, path, ctx) {
      const x = path[0] && bySlug(tab, path[0]);
      if (x) return personPage(container, ctx, tab, title, x, [x.epithet, x.clan, x[key]]);
      const p = page(container);
      p.appendChild(el('h2', { class: 'chapter-h' }, [title]));
      p.appendChild(el('p', { class: 'muted small' }, [lede]));
      if (!list(tab).length) return p.appendChild(empty('met'));
      groups(list(tab), key).forEach((g) => {
        p.appendChild(el('h4', { class: 'fall-group' }, [g.name]));
        p.appendChild(el('div', { class: 'cards' }, g.pages.map((y) => personCard(ctx, tab, y))));
      });
    };
  }

  const tabs = window.VttSiteTabs = window.VttSiteTabs || [];
  tabs.unshift(
    { id: 'home', label: CFG.title || 'Home', render: renderHome, group: 'campaign' },
    { id: 'heralds', label: 'The Heralds', render: peopleTab('heralds', 'The Heralds', 'group', 'Mithras’ heralds, woken beneath London, and those who run with them.'), group: 'campaign' },
    { id: 'people', label: 'Dramatis Personae', render: peopleTab('people', 'Dramatis Personae', 'circle', 'The Kindred and kine the heralds have met, and what they know of them.'), group: 'campaign' },
    { id: 'chronicle', label: 'The Chronicle', render: renderChronicle, group: 'campaign' },
  );
})();
