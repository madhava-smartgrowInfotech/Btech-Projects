"""
Document blocks: content is written once as lists of blocks, then rendered into the
chapter documents, the full report, and (as text) the decks and the paper.
"""

from . import facts as F


def H1(t):
    return ("h1", t)


def H2(t):
    return ("h2", t)


def H3(t):
    return ("h3", t)


def P(t):
    return ("p", t)


def B(*items):
    return ("b", list(items))


def N(*items):
    return ("n", list(items))


def FIG(path, caption, width=5.6):
    return ("fig", path, caption, width)


def TAB(caption, header, rows, widths=None, align=None, size=10):
    return ("tab", caption, header, rows, widths, align, size)


def PAIR(items, width=2.7):
    return ("pair", items, width)


def EQ(text):
    return ("eq", text)


def CODE(text, size=8.5):
    return ("code", text, size)


def render(doc, blocks, h1_page_break=True, skip_h1=False):
    """Render blocks into a kit.Doc."""
    for b in blocks:
        k = b[0]
        if k == "h1":
            if not skip_h1:
                doc.h1(b[1], page_break=h1_page_break)
        elif k == "h2":
            doc.h2(b[1])
        elif k == "h3":
            doc.h3(b[1])
        elif k == "p":
            doc.p(b[1])
        elif k == "b":
            doc.bullets(b[1])
        elif k == "n":
            doc.numbered(b[1])
        elif k == "fig":
            doc.figure(b[1], b[2], b[3])
        elif k == "tab":
            doc.table(b[1], b[2], b[3], b[4], size=b[6], align=b[5])
        elif k == "code":
            doc.code(b[1], b[2])
        elif k == "eq":
            doc.equation(b[1])
        elif k == "pair":
            doc.figure_pair(b[1], b[2])
        else:
            raise ValueError(k)


def plain_text(blocks):
    """All text in the blocks (used by the verifier and for word counts)."""
    out = []
    for b in blocks:
        if b[0] in ("h1", "h2", "h3", "p"):
            out.append(b[1])
        elif b[0] in ("b", "n"):
            out.extend(b[1])
        elif b[0] == "tab":
            out.append(b[1])
            out.extend(b[2])
            for r in b[3]:
                out.extend(str(c) for c in r)
        elif b[0] == "fig":
            out.append(b[2])
        elif b[0] in ("code", "eq"):
            out.append(b[1])
        elif b[0] == "pair":
            out.extend(c for _, c in b[1])
    return "\n".join(out)


import re as _re

_NUM = _re.compile(r"^\d+(\.\d+)*\.?\s+")


def renum(blocks, prefix):
    """Renumber h2/h3 headings of a block list as prefix.n and prefix.n.m (chapter-document numbering)."""
    out, n, m = [], 0, 0
    for b in blocks:
        if b[0] == "h2":
            n, m = n + 1, 0
            out.append(("h2", f"{prefix}.{n} " + _NUM.sub("", b[1])))
        elif b[0] == "h3":
            m += 1
            out.append(("h3", f"{prefix}.{n}.{m} " + _NUM.sub("", b[1])))
        else:
            out.append(b)
    return out
