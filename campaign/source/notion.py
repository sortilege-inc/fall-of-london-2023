"""
notion.py — a Notion HTML export page → blocks, for absorb_notion.py (the GM seed).

One reader for every page, so the converter knows the export's shape once: the page body only
(the title, the property table and the table of contents are the page's furniture); blocks are
headings, paragraphs, list items (with depth), quotes, images, rules and database tables; inline
bold/italic/code/links become the GM text's small Markdown (engine/gm-text.js).

    blocks(path) → [ {kind: 'h', level, text} | {kind: 'p', text} | {kind: 'li', depth, text}
                   | {kind: 'quote', text} | {kind: 'img', src} | {kind: 'hr'}
                   | {kind: 'table', rows: [[cell text]]} ]
"""
import html
import re
from html.parser import HTMLParser

BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "blockquote", "summary", "figcaption", "td", "th", "div"}


class _Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.buf = []
        self.stack = []          # open tags
        self.skip = 0            # inside nav / style / header / the property table
        self.list_depth = 0
        self.in_body = False
        self.table = None        # rows while inside a <table>
        self.row = None
        self.href = []

    # inline text
    def _emit_text(self, s):
        if self.skip or not self.in_body:
            return
        self.buf.append(s)

    def _flush(self, kind, **kw):
        text = re.sub(r"[ \t\r\f\v]+", " ", "".join(self.buf)).strip()
        text = re.sub(r"\s*\n\s*", "\n", text)
        self.buf = []
        if self.row is not None and kind == "cell":
            self.row.append(text)
            return
        if not text:
            return
        self.out.append(dict(kind=kind, text=text, **kw))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "page-body" in (a.get("class") or ""):
            self.in_body = True
        if not self.in_body:
            return
        if tag in ("nav", "style", "script"):
            self.skip += 1
        self.stack.append(tag)
        if self.skip:
            return
        if tag in ("p", "h1", "h2", "h3", "h4", "blockquote", "summary", "li", "ul", "ol", "figure", "details"):
            # a block opening inside another (a list nested in a list item, a toggle's body): what
            # the outer block said so far is its own block, not lost to the inner one
            if "".join(self.buf).strip():
                outer = next((s for s in reversed(self.stack[:-1]) if s in ("li", "p", "blockquote", "summary")), None)
                self._flush("li" if outer == "li" else "p", **({"depth": self.list_depth} if outer == "li" else {}))
            self.buf = []
        if tag == "span" and "selected-value" in (a.get("class") or "") and "".join(self.buf).strip():
            self.buf.append(", ")
        if tag in ("ul", "ol"):
            self.list_depth += 1
        elif tag == "table":
            self.table = []
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.buf = []
        elif tag == "img":
            self.out.append(dict(kind="img", src=a.get("src", "")))
        elif tag == "hr":
            self.out.append(dict(kind="hr"))
        elif tag == "br":
            self.buf.append("\n")
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "i"):
            self.buf.append("*")
        elif tag == "code":
            self.buf.append("`")
        elif tag == "a":
            href = a.get("href") or ""
            self.href.append(href if href.startswith("http") else "")
            if self.href[-1]:
                self.buf.append("[")

    def handle_endtag(self, tag):
        if not self.in_body or not self.stack:
            return
        # close up to the matching tag (Notion's HTML is well formed; this is belt and braces)
        while self.stack:
            t = self.stack.pop()
            if t in ("nav", "style", "script"):
                self.skip -= 1
            if t == tag:
                break
        if self.skip and tag not in ("nav", "style", "script"):
            return
        if tag in ("h1", "h2", "h3", "h4"):
            self._flush("h", level=int(tag[1]))
        elif tag in ("p", "summary", "figcaption", "figure"):
            self._flush("p")
        elif tag == "blockquote":
            self._flush("quote")
        elif tag == "li":
            self._flush("li", depth=self.list_depth)
        elif tag in ("ul", "ol"):
            self.list_depth -= 1
        elif tag in ("td", "th"):
            self._flush("cell")
        elif tag == "tr":
            if self.table is not None and self.row is not None:
                self.table.append(self.row)
            self.row = None
        elif tag == "table":
            if self.table:
                self.out.append(dict(kind="table", rows=self.table))
            self.table = None
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "i"):
            self.buf.append("*")
        elif tag == "code":
            self.buf.append("`")
        elif tag == "a":
            href = self.href.pop() if self.href else ""
            if href:
                self.buf.append("](%s)" % href)
        elif tag == "div" and self.buf and "".join(self.buf).strip() and self.row is None:
            # text sitting directly in a div (Notion's bookmark/"source" figures)
            self._flush("p")

    def handle_data(self, data):
        self._emit_text(data)


def _tidy(text):
    # empty emphasis markers Notion leaves around spaces, and doubled markers
    text = re.sub(r"\*\*(\s*)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(\s*)\*(?!\*)", r"\1", text)
    return text.strip()


def blocks(path):
    r = _Reader()
    r.feed(open(path, encoding="utf-8").read())
    out = []
    for b in r.out:
        if "text" in b:
            b["text"] = _tidy(b["text"])
            if not b["text"] or b["text"] in ("**", "*"):
                continue
        out.append(b)
    return out


def plain_words(path):
    """The page body's words, straight from the HTML with no structure — the checker's own reading,
    sharing nothing with the reader above but the page-body boundary and the nav it skips."""
    t = open(path, encoding="utf-8").read()
    t = t[t.index('<div class="page-body"'):]
    t = re.sub(r"<nav\b.*?</nav>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return words(html.unescape(t))


def words(text):
    return re.findall(r"[0-9A-Za-zÀ-ÿ’'Ā-ɏ]+", text.replace("’", "'"))
