#!/usr/bin/env python3
"""Build p-rick site blog pages from markdown blog posts (dual-theme site)."""
import os
import re
import html as html_mod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOGS_MD = os.path.join(BASE, 'blogs')
BLOG_OUT = os.path.join(BASE, 'blog')

BLOGS = [
    ('2026-10-07-your-phone-sees-everything.md', 'blog/p001.html', 'P-001',
     'The Personal Event Bus', 'p-001'),
    ('2026-10-07-largest-unclaimed-money.md', 'blog/p002.html', 'P-002',
     'Consumer Entitlements as Dead Capital', 'p-002'),
    ('2026-10-07-your-inflation-is-not-the-cpi.md', 'blog/p003.html', 'P-003',
     'The n=1 Cost-of-Living Index', 'p-003'),
    ('2026-10-07-your-software-has-a-second-behavior.md', 'blog/p004.html', 'P-004',
     'Degradation Contracts', 'p-004'),
    ('2026-10-07-files-forgot-who-they-are.md', 'blog/p005.html', 'P-005',
     'Provenance-Native Storage', 'p-005'),
    ('2026-10-07-the-most-important-scheduler.md', 'blog/p006.html', 'P-006',
     'The Attention Scheduler', 'p-006'),
    ('2026-10-07-you-own-a-distributed-computer.md', 'blog/p007.html', 'P-007',
     'The Intermittent Compute Fabric', 'p-007'),
]

NO_FLASH = (
    "<script>(function(){try{var t=localStorage.getItem('p-rick-theme');"
    "if(!t){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}"
    "document.documentElement.setAttribute('data-theme',t);}"
    "catch(e){document.documentElement.setAttribute('data-theme','dark');}})();</script>"
)

TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — p-rick</title>
<meta name="description" content="{desc}">
{noflash}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="../index.html"><span class="brand-mark">p-rick</span><span class="brand-sub">research</span></a>
  <div class="header-right">
    <nav><a href="../papers.html">Papers</a><a href="../blog.html">Blog</a><a href="../index.html#about">About</a><a href="https://github.com/srivtx/p-rick">GitHub</a></nav>
    <button class="theme-toggle" aria-label="Toggle dark / light mode" title="Toggle dark / light mode">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
  </div>
</header>
<main class="blog-main">
  <article class="post">
    <div class="post-kicker">essay &middot; companion to {paper}</div>
    <h1 class="post-title">{title}</h1>
    <div class="post-meta">{date} &middot; p-rick research program</div>
    {body}
    <div class="post-footer">
      <p>This essay accompanies the research paper <a href="../pdfs/{pdf}.pdf">{paper_full} (PDF)</a>.
      Working papers and sources live in the <a href="https://github.com/srivtx/p-rick">p-rick repository</a>;
      the work ledger is <a href="https://github.com/srivtx/p-rick/blob/main/agents.md">agents.md</a>.</p>
    </div>
  </article>
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <div>
      <div class="f-brand">p-rick</div>
      <div class="f-note">an independent research program on missing software &middot; papers, PDFs, essays</div>
    </div>
    <div class="footer-links">
      <a href="../index.html">Home</a><a href="../papers.html">Papers</a><a href="../blog.html">Blog</a><a href="https://github.com/srivtx/p-rick">GitHub</a>
    </div>
  </div>
</footer>
<script src="../assets/theme.js"></script>
</body>
</html>
"""


def inline(s):
    s = html_mod.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\w)\*([^*\n]+)\*(?!\w)', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def md_to_html(md):
    lines = md.split('\n')
    out = []
    in_list = None
    para = []

    def flush_para():
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>')
            para.clear()

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append('</%s>' % in_list)
            in_list = None

    for raw in lines:
        ln = raw.rstrip()
        if not ln.strip():
            flush_para()
            flush_list()
            continue
        if ln.startswith('### '):
            flush_para(); flush_list()
            out.append('<h3>' + inline(ln[4:]) + '</h3>')
        elif ln.startswith('## '):
            flush_para(); flush_list()
            out.append('<h2>' + inline(ln[3:]) + '</h2>')
        elif ln.startswith('# '):
            flush_para(); flush_list()
            out.append('<h2>' + inline(ln[2:]) + '</h2>')  # post title is the h1 already
        elif re.match(r'^[-*] ', ln):
            flush_para()
            if in_list != 'ul':
                flush_list(); out.append('<ul>'); in_list = 'ul'
            out.append('<li>' + inline(ln[2:]) + '</li>')
        elif re.match(r'^\d+\. ', ln):
            flush_para()
            if in_list != 'ol':
                flush_list(); out.append('<ol>'); in_list = 'ol'
            out.append('<li>' + inline(re.sub(r'^\d+\. ', '', ln)) + '</li>')
        elif ln.startswith('> '):
            flush_para(); flush_list()
            out.append('<blockquote><p>' + inline(ln[2:]) + '</p></blockquote>')
        elif ln.strip() in ('---', '***'):
            flush_para(); flush_list()
            out.append('<hr>')
        else:
            flush_list()
            para.append(ln.strip())

    flush_para()
    flush_list()
    return '\n    '.join(out)


def parse_front_matter(md):
    fm = {}
    body = md
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', md, re.S)
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    return fm, body


def main():
    os.makedirs(BLOG_OUT, exist_ok=True)
    for md_name, out_rel, paper, paper_full, pdf in BLOGS:
        path = os.path.join(BLOGS_MD, md_name)
        if not os.path.exists(path):
            print('MISSING:', md_name)
            continue
        raw = open(path, encoding='utf-8').read()
        fm, body_md = parse_front_matter(raw)
        title = fm.get('title', md_name)
        date = fm.get('date', '')
        # strip leading "# Title" dup (title is in the h1)
        body_md = re.sub(r'^#\s+.*\n+', '', body_md, count=1)
        desc = re.sub(r'[<>]', '', inline(body_md[:180]).replace('<p>', '').replace('</p>', '')) + '…'
        body = md_to_html(body_md)
        html_out = TEMPLATE.format(
            noflash=NO_FLASH, title=inline(title), desc=desc.strip()[:300],
            paper=paper, paper_full=paper_full, date=date, body=body, pdf=pdf)
        out_path = os.path.join(BASE, out_rel)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        open(out_path, 'w', encoding='utf-8').write(html_out)
        print('wrote', out_rel, '(%d chars)' % len(html_out))


if __name__ == '__main__':
    main()
