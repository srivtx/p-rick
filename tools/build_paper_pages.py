#!/usr/bin/env python3
"""Build designed paper pages (paper/p001.html .. paper/p026.html) from papers/*.md.

Reading edition of each working paper: abstract block, sticky contents,
figures with numbered captions, KaTeX math (math papers only), theorem
boxes, styled tables, prev/next nav, BibTeX. Title links on papers.html
point here; the .md source stays one click away.
"""
import os
import re
import glob
import html as html_mod

from pp_template import (TEMPLATE, MASTHEAD, FOOTER, NO_FLASH, KATEX,
                         SCROLLSPY, SITE, GH)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(BASE, 'papers')
OUT_DIR = os.path.join(BASE, 'paper')

SERIES_FULL = {
    'I': 'User-owned data', 'II': 'Systems', 'III': 'Continuity',
    'IV': 'Assumptions', 'V': 'Promises', 'VI': 'Laws', 'VII': 'Collapse',
    'VIII': 'Machinery',
}

# ── math detection ────────────────────────────────────────────────────

def has_math(text):
    if '$$' in text:
        return True
    inline = re.findall(r'(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)', text)
    latexish = [m for m in inline if '\\' in m or '^' in m or '_{' in m]
    return len(latexish) >= 5


# ── markdown → HTML ───────────────────────────────────────────────────

class Stash:
    """Placeholder stash: code fences and (optionally) math survive inline
    formatting untouched; restored at the very end."""

    def __init__(self, math_mode):
        self.items = []
        self.math_mode = math_mode

    def put(self, raw, kind):
        self.items.append((kind, raw))
        return '\x00%d\x00' % (len(self.items) - 1)

    def extract(self, text):
        # fenced code
        text = re.sub(r'```(\w*)\n(.*?)\n```', lambda m: self.put(m.group(2), 'code'), text, flags=re.S)
        if self.math_mode:
            # display math first
            text = re.sub(r'\$\$(.+?)\$\$', lambda m: self.put(m.group(0), 'math'), text, flags=re.S)
            # inline math: single $ pairs, no newline inside
            text = re.sub(r'(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)', lambda m: self.put(m.group(0), 'math'), text)
        return text

    def restore(self, html_out):
        def sub(m):
            kind, raw = self.items[int(m.group(1))]
            if kind == 'code':
                return '<pre class="code"><code>%s</code></pre>' % html_mod.escape(raw)
            return raw  # math: raw source for KaTeX
        return re.sub(r'\x00(\d+)\x00', sub, html_out)


def inline_md(s, stash):
    s = html_mod.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'\*\*\*([^*]+)\*\*\*', r'<strong><em>\1</em></strong>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


THM_RE = re.compile(
    r'^\*\*(Lemma|Theorem|Proposition|Corollary|Definition|Claim|Result|'
    r'Observation|Remark|Property|Principle|Law|Model)\s*([\d.]*\.?)\*\*\s*(.*)',
    re.S)


def slugify(sect_no, title):
    return 's' + re.sub(r'\W', '', sect_no.rstrip('.')) if sect_no else re.sub(
        r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]


def convert(body_md, stash):
    """Block-level markdown conversion. Returns (html, toc_entries, figs)."""
    lines = body_md.split('\n')
    out, toc, figs = [], [], []
    in_list = None   # 'ul' | 'ol'
    para = []

    def flush_para():
        if not para:
            return
        text = ' '.join(para)
        para.clear()
        # paragraph that is only display math -> centered block
        pm = re.match(r'^\x00(\d+)\x00\.?\s*$', text)
        if pm:
            kind, raw = stash.items[int(pm.group(1))]
            if kind == 'math':
                out.append('<div class="math-display">%s</div>' % raw)
                return
        m = THM_RE.match(text)
        if m:
            head = (m.group(1) + (' ' + m.group(2).rstrip('.') if m.group(2) else '')).strip()
            rest = inline_md(m.group(3), stash)
            out.append('<div class="thm"><p><span class="thm-head">%s.</span> %s</p></div>'
                       % (html_mod.escape(head), rest))
            return
        out.append('<p>' + inline_md(text, stash) + '</p>')

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append('</%s>' % in_list)
            in_list = None

    def close_table(rows):
        if len(rows) < 2:
            for r in rows:
                out.append('<p>' + inline_md(r, stash) + '</p>')
            return
        header = [c.strip() for c in rows[0].strip().strip('|').split('|')]
        aligns = []
        for c in rows[1].strip().strip('|').split('|'):
            c = c.strip()
            aligns.append('center' if re.match(r'^:-+:$', c) else
                          'right' if c.endswith(':') else 'left')
        h = ['<div class="tbl-wrap"><table class="paper-table">']
        # symbol-like columns (all cells short) render centered for scanability
        body_rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows[2:]]
        ncols = len(header)
        center_col = []
        for ci in range(ncols):
            cells = [r[ci] if ci < len(r) else '' for r in body_rows]
            center_col.append(bool(cells) and all(len(c) <= 4 for c in cells))
        h.append('<thead><tr>')
        for i, c in enumerate(header):
            a = ' class="ta-%s"' % aligns[i] if i < len(aligns) and aligns[i] != 'left' else ''
            h.append('<th%s>%s</th>' % (a, inline_md(c, stash)))
        h.append('</tr></thead><tbody>')
        for r in rows[2:]:
            cells = [c.strip() for c in r.strip().strip('|').split('|')]
            h.append('<tr>')
            for i, c in enumerate(cells):
                a = ' class="ta-%s"' % aligns[i] if (i < len(aligns) and aligns[i] != 'left' or center_col[i]) else ''
                h.append('<td%s>%s</td>' % (a, inline_md(c, stash)))
            h.append('</tr>')
        h.append('</tbody></table></div>')
        out.append(''.join(h))

    tbl_rows = []

    def flush_table():
        nonlocal tbl_rows
        if tbl_rows:
            close_table(tbl_rows)
            tbl_rows = []

    for raw in lines:
        ln = raw.rstrip()
        if not ln.strip():
            flush_para(); flush_list(); flush_table()
            continue
        # tables
        if re.match(r'^\s*\|.+\|\s*$', ln):
            flush_para(); flush_list()
            tbl_rows.append(ln)
            continue
        flush_table()
        # figures
        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', ln)
        if m:
            flush_para(); flush_list()
            figs.append((m.group(1), m.group(2)))
            n = len(figs)
            out.append(
                '<figure class="paper-fig" id="f%d">'
                '<a href="%s" target="_blank" rel="noopener">'
                '<img src="%s" alt="%s" loading="lazy"></a>'
                '<figcaption><span class="fig-no">F%d</span>%s</figcaption></figure>'
                % (n, m.group(2), m.group(2), html_mod.escape(m.group(1)), n,
                   inline_md(m.group(1), stash)))
            continue
        if ln.startswith('#### '):
            flush_para(); flush_list()
            out.append('<h4>' + inline_md(ln[5:], stash) + '</h4>')
        elif ln.startswith('### '):
            flush_para(); flush_list()
            t = ln[4:]
            mn = re.match(r'^([\d.]+)\s+(.*)', t)
            sid, label = (slugify(mn.group(1), mn.group(2)), t) if mn else (
                re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')[:40], t)
            out.append('<h3 id="%s">%s</h3>' % (sid, inline_md(label, stash)))
        elif ln.startswith('## '):
            flush_para(); flush_list()
            t = ln[3:]
            mn = re.match(r'^([\d.]+)\s+(.*)', t)
            if mn:
                sid = slugify(mn.group(1), mn.group(2))
                toc.append((sid, mn.group(1).rstrip('.'), inline_md(mn.group(2), stash)))
                out.append('<h2 id="%s"><span class="secno">%s</span>%s</h2>'
                           % (sid, mn.group(1), inline_md(mn.group(2), stash)))
            else:
                sid = re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')[:40]
                toc.append((sid, '', inline_md(t, stash)))
                out.append('<h2 id="%s">%s</h2>' % (sid, inline_md(t, stash)))
        elif ln.startswith('# '):
            flush_para(); flush_list()  # title handled elsewhere
        elif re.match(r'^[-*]\s+', ln):
            flush_para()
            if in_list != 'ul':
                flush_list(); out.append('<ul>'); in_list = 'ul'
            out.append('<li>' + inline_md(re.sub(r'^[-*]\s+', '', ln), stash) + '</li>')
        elif re.match(r'^\d+\.\s+', ln):
            flush_para()
            if in_list != 'ol':
                flush_list(); out.append('<ol>'); in_list = 'ol'
            out.append('<li>' + inline_md(re.sub(r'^\d+\.\s+', '', ln), stash) + '</li>')
        elif ln.startswith('> '):
            flush_para(); flush_list()
            out.append('<blockquote><p>' + inline_md(ln[2:], stash) + '</p></blockquote>')
        elif ln.strip() in ('---', '***', '___'):
            flush_para(); flush_list()
            out.append('<hr>')
        else:
            flush_list()
            para.append(ln.strip())

    flush_para(); flush_list(); flush_table()
    return '\n'.join(out), toc, figs


# ── paper metadata ────────────────────────────────────────────────────

META_RE = re.compile(
    r'\*\*p-rick working paper (P-\d{3})\s*[·\s]+series ([IV]+)\s*\(([^)]+)\)'
    r'\s*[·\s]+draft ([\d.]+)([^(]*)\(([^)]*)\)\*\*')

def paper_meta(text, fname):
    """Extract id, series, series-name, draft, revision note, title."""
    fm, body = {}, text
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.S)
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    title = fm.get('title')
    if not title:
        t = re.match(r'^#\s+(.+)$', body, re.M)
        title = t.group(1).strip() if t else fname
    meta = {'pid': None, 'series': None, 'series_name': None,
            'draft': '1.0', 'rev_note': ''}
    mm = META_RE.search(body)
    if mm:
        meta['pid'] = mm.group(1)
        meta['series'] = mm.group(2)
        meta['series_name'] = mm.group(3).strip()
        meta['draft'] = mm.group(4).strip()
        # revision parenthetical if the trailing text carries one
        tail = body[mm.end():body.find('\n', mm.end())] if '\n' in body[mm.end():] else body[mm.end():]
        rpm = re.search(r'\(([^)]+)\)', tail)
        if rpm and 'revis' in rpm.group(1).lower():
            meta['rev_note'] = rpm.group(1).strip()
    else:
        n = int(re.match(r'.*p-(\d{3})', fname).group(1))
        meta['pid'] = 'P-%03d' % n
        meta['series'] = {1: 'I', 2: 'I', 3: 'I'}.get(n, '')
        meta['series_name'] = SERIES_FULL.get(meta['series'], '')
    return title, meta, body


def split_sections(body):
    """Split abstract / revision-note / keywords / rest."""
    revision = ''
    m = re.search(r'^\*Revision note\.\*\s*(.+?)(?=\n\n|\n##)', body, re.S | re.M)
    if m:
        revision = m.group(1).strip()
    am = re.search(r'^##\s*Abstract\s*\n\n?(.+?)(?=\n\n\*\*Keywords|\n##)', body, re.S)
    abstract = am.group(1).strip() if am else ''
    km = re.search(r'\*\*Keywords:\*\*\s*(.+)', body)
    keywords = [k.strip() for k in km.group(1).split(',') if k.strip()] if km else []
    # body proper: from first numbered section (or first ## after abstract)
    bm = re.search(r'^##\s', body[body.find('## Abstract') + 11 if '## Abstract' in body else 0:], re.M)
    start = (body.find('## Abstract') + 11 if '## Abstract' in body else 0)
    rest = body[start:]
    ns = re.search(r'^## ', rest.strip(), re.M)
    body_md = rest.strip()
    if ns:
        body_md = rest.strip()[ns.start():]
    return revision, abstract, keywords, body_md


def bibtex(pid, title, series, year=2026):
    n = int(pid.split('-')[1])
    return ("@techreport{prick2026p%03d,\n"
            "  title       = {%s},\n"
            "  author      = {p-rick research program},\n"
            "  institution = {p-rick},\n"
            "  type        = {Working paper},\n"
            "  number      = {%s},\n"
            "  series      = {Series %s: %s},\n"
            "  year        = {2026},\n"
            "  month       = oct,\n"
            "  url         = {%s/paper/p%03d.html},\n"
            "  note        = {srivtx.github.io/p-rick}\n}"
            % (n, title.replace('{', '').replace('}', ''), pid, series,
               SERIES_FULL.get(series, ''), SITE, n))


# ── build ─────────────────────────────────────────────────────────────

def build():
    files = sorted(glob.glob(os.path.join(PAPERS_DIR, 'p-*.md')))
    papers = []
    for f in files:
        fname = os.path.basename(f)
        n = int(re.match(r'p-(\d{3})', fname).group(1))
        text = open(f).read()
        title, meta, body = paper_meta(text, fname)
        revision, abstract, keywords, body_md = split_sections(body)
        papers.append(dict(n=n, fname=fname, title=title, meta=meta,
                           revision=revision, abstract=abstract,
                           keywords=keywords, body=body_md, math=has_math(text)))
    os.makedirs(OUT_DIR, exist_ok=True)
    for p in papers:
        stash = Stash(p['math'])
        stashed = stash.extract(p['body'])
        body_html, toc, figs = convert(stashed, stash)
        body_html = stash.restore(body_html)
        abstract_html = stash.restore(inline_md(stash.extract(p['abstract']), stash)) if p['math'] \
            else inline_md(p['abstract'], stash)
        revision_html = inline_md(p['revision'], stash) if p['revision'] else ''

        pid = p['meta']['pid']
        n = p['n']
        date_iso = '2026-10-09' if (n >= 24 or p['meta']['draft'] != '1.0') else '2026-10-07'
        ser = p['meta']['series']
        series_label = '%s &middot; %s' % (ser, html_mod.escape(p['meta']['series_name'])) if p['meta']['series_name'] else ser
        draft = p['meta']['draft']
        meta_line = ('%s &middot; draft %s &middot; p-rick research program &middot; '
                     '<a href="%s/blob/main/papers/%s">source</a> &middot; <a href="../pdfs/p-%03d.pdf">pdf</a> &middot; cc by 4.0'
                     % (date_iso, draft, GH, p['fname'], n))
        if p['meta']['rev_note']:
            meta_line += ' &middot; <span class="rev-flag">revised</span>'
        kw_html = ''.join('<span class="kw">%s</span>' % html_mod.escape(k) for k in p['keywords']) \
            or '<span class="kw">—</span>'
        toc_html = '<ol>' + ''.join(
            '<li%s><a href="#%s"><span class="tocn">%s</span>%s</a></li>'
            % (' class="toc-sub"' if not no else '', sid, no + '.', t)
            for sid, no, t in toc if no) + '</ol>'
        # unnumbered headings (References etc.) get their own trailing list
        toc_html += '<ul class="toc-extra">' + ''.join(
            '<li><a href="#%s">%s</a></li>' % (sid, t) for sid, no, t in toc if not no) + '</ul>'

        harness = None
        for cand in ('p-%03d-simulation.py' % n,):
            if os.path.exists(os.path.join(BASE, 'code', cand)):
                harness = cand
        if not harness:
            hb = sorted(glob.glob(os.path.join(BASE, 'code', 'p-%03db-*.py' % n)))
            if hb:
                harness = os.path.basename(hb[0])
        harness_link = ('        <a class="pa" href="%s/blob/main/code/%s">harness&thinsp;.py</a>'
                        % (GH, harness)) if harness else ''

        prev = next_ = ''
        if n > 1:
            q = papers[n - 2]
            prev = ('<a class="pn pn-prev" href="p%03d.html"><span class="pn-k">&larr; previous</span>'
                    '<span class="pn-t">%s</span></a>' % (q['n'], html_mod.escape(q['title'])))
        if n < len(papers):
            q = papers[n]
            next_ = ('<a class="pn pn-next" href="p%03d.html"><span class="pn-k">next &rarr;</span>'
                     '<span class="pn-t">%s</span></a>' % (q['n'], html_mod.escape(q['title'])))

        revision_block = ''
        if p['revision']:
            revision_block = ('<aside class="paper-revision"><span class="rev-label">revision note</span>'
                              '<p>%s</p></aside>' % revision_html)

        desc = re.sub(r'[*$`]', '', p['abstract'])[:280].rsplit(' ', 1)[0] + ' …'
        jsonld = ('{"@context":"https://schema.org","@type":"ScholarlyArticle",'
                  '"headline":%s,"author":{"@type":"Organization","name":"p-rick research program"},'
                  '"datePublished":"%s","license":"https://creativecommons.org/licenses/by/4.0/",'
                  '"isPartOf":"%s","identifier":"%s","url":"%s/paper/p%03d.html"}'
                  % (_j(p['title']), date_iso, SITE, pid, SITE, n))

        page = TEMPLATE.format(
            title=html_mod.escape(p['title']), pid=pid,
            desc=html_mod.escape(desc), og_url='%s/paper/p%03d.html' % (SITE, n),
            site=SITE, date_iso=date_iso, noflash=NO_FLASH,
            katex=KATEX if p['math'] else '',
            jsonld=jsonld, masthead=MASTHEAD,
            series_label=series_label, meta_line=meta_line,
            pdf='p-%03d' % n, src_url='%s/blob/main/papers/%s' % (GH, p['fname']),
            essay='p%03d' % n, harness_link=harness_link,
            revision=revision_block, abstract=abstract_html, keywords=kw_html,
            toc=toc_html, body=body_html, prev=prev, next=next_,
            bibtex=bibtex(pid, p['title'], ser), footer=FOOTER, scrollspy=SCROLLSPY,
        )
        out = os.path.join(OUT_DIR, 'p%03d.html' % n)
        open(out, 'w').write(page)
        print('built %s  (%d sections, %d figures, math=%s, %d chars)'
              % (os.path.basename(out), len(toc), len(figs), p['math'], len(page)))


def _j(s):
    import json
    return json.dumps(s)


if __name__ == '__main__':
    build()
